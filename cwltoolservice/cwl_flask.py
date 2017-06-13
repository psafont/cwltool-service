import os
from subprocess import Popen, PIPE
from tempfile import mkstemp, mkdtemp
from json import dumps, loads
from signal import SIGQUIT, SIGTSTP, SIGCONT
from threading import Lock, Thread
from time import sleep
from copy import copy
from yaml import load

from future.utils import iteritems

from flask import Flask, Response, request, redirect, abort, send_from_directory
from flask_cors import CORS

APP = Flask(__name__)
CORS(APP)

JOBS_LOCK = Lock()
JOBS = []


class Job(Thread):
    # pylint: disable=too-many-instance-attributes
    def __init__(self, jobid, path, inputobj):
        super(Job, self).__init__()
        self.jobid = jobid
        self.path = path
        self.inputobj = inputobj
        self.status = {
            "id": "%sjobs/%i" % (request.url_root, self.jobid),
            "log": "%sjobs/%i/log" % (request.url_root, self.jobid),
            "run": self.path,
            "state": "Running",
            "input": loads(self.inputobj),
            "output": None
        }

        self.stdoutdata = self.stderrdata = None
        self.updatelock = Lock()

        with self.updatelock:
            loghandle, self.logname = mkstemp()
            self.outdir = mkdtemp()
            self.proc = Popen(["cwl-runner", "--leave-outputs", self.path, "-"],
                              stdin=PIPE,
                              stdout=PIPE,
                              stderr=loghandle,
                              close_fds=True,
                              cwd=self.outdir)

    def run(self):
        self.stdoutdata, self.stderrdata = self.proc.communicate(self.inputobj)
        if self.proc.returncode == 0:
            outobj = load(self.stdoutdata)
            with self.updatelock:
                self.status["state"] = "Complete"
                self.status["output"] = outobj
        else:
            with self.updatelock:
                self.status["state"] = "Error"

    def getstatus(self):
        with self.updatelock:
            return self.status.copy()

    def cancel(self):
        if self.status["state"] == "Running":
            self.proc.send_signal(SIGQUIT)
            with self.updatelock:
                self.status["state"] = "Canceled"

    def pause(self):
        if self.status["state"] == "Running":
            self.proc.send_signal(SIGTSTP)
            with self.updatelock:
                self.status["state"] = "Paused"

    def resume(self):
        if self.status["state"] == "Paused":
            self.proc.send_signal(SIGCONT)
            with self.updatelock:
                self.status["state"] = "Running"


@APP.route("/run", methods=['POST'])
def runworkflow():
    path = request.args["wf"]
    with JOBS_LOCK:
        jobid = len(JOBS)
        job = Job(jobid, path, request.stream.read())
        job.start()
        JOBS.append(job)
    return redirect("/jobs/%i" % jobid, code=303)


@APP.route("/jobs/<int:jobid>", methods=['GET', 'POST'])
def jobcontrol(jobid):
    job = getjob(jobid)
    if not job:
        return abort(404)

    if request.method == 'POST':
        action = request.args.get("action")
        if action:
            if action == "cancel":
                job.cancel()
            elif action == "pause":
                job.pause()
            elif action == "resume":
                job.resume()

    status = job.getstatus()

    # replace location so web clients can retrieve any outputs
    if status["state"] == "Complete":
        for name, output in iteritems(status["output"]):
            output["location"] = '/'.join([request.host_url[:-1],
                                           "jobs", str(jobid), "output", name])

    return dumps(status, indent=4), 200, ""


@APP.route("/jobs/<int:jobid>/log", methods=['GET'])
def getlog(jobid):
    job = getjob(jobid)
    if not job:
        return abort(404)

    return Response(logspooler(job))


@APP.route("/jobs/<int:jobid>/output/<string:outputid>", methods=['GET'])
def getoutput(jobid, outputid):
    job = getjob(jobid)
    if not job:
        return abort(404)

    output = getoutputobj(job, outputid)
    if not output:
        return abort(404)

    (path, filename) = getfile(output)
    if not path or not filename:
        return abort(404)

    return send_from_directory(path, filename)


@APP.route("/jobs", methods=['GET'])
def getjobs():
    with JOBS_LOCK:
        jobs = copy(JOBS)
    return Response(spool(jobs))


def getoutputobj(job, outputid):
    # TODO deal with attacks and exceptions
    return job.status["output"][outputid]


def getfile(output):
    return os.path.split(output["path"])


def getjob(jobid):
    job = ""
    with JOBS_LOCK:
        if 0 <= jobid < len(JOBS):
            job = JOBS[jobid]
    return job


def spool(jobs):
    yield "["
    connector = ""
    for job in jobs:
        yield connector + dumps(job.getstatus(), indent=4)
        if connector == "":
            connector = ", "
    yield "]"


def logspooler(job):
    with open(job.logname, "r") as logfile:
        while True:
            buf = logfile.read(4096)
            if buf:
                yield buf
            else:
                with job.updatelock:
                    if job.status["state"] != "Running":
                        break
                sleep(1)


if __name__ == "__main__":
    # app.debug = True
    APP.run('0.0.0.0')

from os import path
from subprocess import Popen, PIPE
from tempfile import mkstemp, mkdtemp
from json import dumps, loads
from yaml import load
from signal import SIGQUIT, SIGTSTP, SIGCONT
from threading import Lock, Thread
from time import sleep
from copy import copy

from future.utils import iteritems

from flask import Flask, Response, request, redirect, abort, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

jobs_lock = Lock()
jobs = []


class Job(Thread):
    def __init__(self, jobid, path, inputobj):
        super(Job, self).__init__()
        self.jobid = jobid
        self.path = path
        self.inputobj = inputobj
        self.updatelock = Lock()
        self.begin()

    def begin(self):
        loghandle, self.logname = mkstemp()
        with self.updatelock:
            self.outdir = mkdtemp()
            self.proc = Popen(["cwl-runner", "--leave-outputs", self.path, "-"],
                              stdin=PIPE,
                              stdout=PIPE,
                              stderr=loghandle,
                              close_fds=True,
                              cwd=self.outdir)
            self.status = {
                "id": "%sjobs/%i" % (request.url_root, self.jobid),
                "log": "%sjobs/%i/log" % (request.url_root, self.jobid),
                "run": self.path,
                "state": "Running",
                "input": loads(self.inputobj),
                "output": None
            }

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


@app.route("/run", methods=['POST'])
def runworkflow():
    path = request.args["wf"]
    with jobs_lock:
        jobid = len(jobs)
        job = Job(jobid, path, request.stream.read())
        job.start()
        jobs.append(job)
    return redirect("/jobs/%i" % jobid, code=303)


@app.route("/jobs/<int:jobid>", methods=['GET', 'POST'])
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

    #replace location so web clients can retrieve any outputs
    if status["state"] == "Complete":
        for name, output in iteritems(status["output"]):
            output["location"] = '/'.join([request.host_url[:-1], "jobs", str(jobid), "output", name])

    return dumps(status, indent=4), 200, ""


@app.route("/jobs/<int:jobid>/log", methods=['GET'])
def getlog(jobid):
    job = getjob(jobid)
    if not job:
        return abort(404)

    return Response(logspooler(job))


@app.route("/jobs/<int:jobid>/output/<string:outputid>", methods=['GET'])
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


@app.route("/jobs", methods=['GET'])
def getjobs():
    with jobs_lock:
        jobscopy = copy(jobs)
    return Response(spool(jobscopy))


def getoutputobj(job, outputid):
    # TODO deal with attacks and exceptions
    return job.status["output"][outputid]


def getfile(output):
    return path.split(output["path"])


def getjob(jobid):
    job = ""
    with jobs_lock:
        if 0 <= jobid < len(jobs):
            job = jobs[jobid]
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
    with open(job.logname, "r") as f:
        while True:
            r = f.read(4096)
            if r:
                yield r
            else:
                with job.updatelock:
                    if job.status["state"] != "Running":
                        break
                sleep(1)

if __name__ == "__main__":
    #app.debug = True
    app.run()

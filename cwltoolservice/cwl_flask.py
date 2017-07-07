import os
from copy import copy
from json import dumps
from threading import Lock
from time import sleep

from flask import Flask, Response, request, redirect, abort, send_from_directory
from flask_cors import CORS
from future.utils import iteritems

from cwltoolservice.job import Job

APP = Flask(__name__)
CORS(APP)

JOBS_LOCK = Lock()
JOBS = []


@APP.route('/run', methods=[u'POST'])
def runworkflow():
    path = request.args[u'wf']
    with JOBS_LOCK:
        jobid = len(JOBS)
        job = Job(jobid, path, request.stream.read())
        job.start()
        JOBS.append(job)
    return redirect(u'/jobs/%i' % jobid, code=303)


@APP.route(u'/jobs/<int:jobid>', methods=[u'GET', u'POST'])
def jobcontrol(jobid):
    job = getjob(jobid)
    if not job:
        return abort(404)

    if request.method == u'POST':
        action = request.args.get(u'action')
        if action:
            if action == u'cancel':
                job.cancel()
            elif action == u'pause':
                job.pause()
            elif action == u'resume':
                job.resume()

    status = job.getstatus()

    # replace location so web clients can retrieve any outputs
    if status[u'state'] == u'Complete':
        for name, output in iteritems(status[u'output']):
            output[u'location'] = u'/'.join([request.host_url[:-1],
                                             u'jobs', str(jobid), u'output', name])

    return dumps(status, indent=4), 200, u''


@APP.route(u'/jobs/<int:jobid>/log', methods=[u'GET'])
def getlog(jobid):
    job = getjob(jobid)
    if not job:
        return abort(404)

    return Response(logspooler(job))


@APP.route(u'/jobs/<int:jobid>/output/<string:outputid>', methods=[u'GET'])
def getoutput(jobid, outputid):
    job = getjob(jobid)
    if not job:
        return abort(404)

    output = getoutputobj(job.status, outputid)
    if not output:
        return abort(404)

    (path, filename) = getfile(output)
    if not path or not filename:
        return abort(404)

    return send_from_directory(path, filename)


@APP.route(u'/jobs', methods=[u'GET'])
def getjobs():
    with JOBS_LOCK:
        jobs = copy(JOBS)
    return Response(spool(jobs))


def getoutputobj(status, outputid):
    try:
        return status[u'output'][outputid]
    except KeyError:
        return None


def getfile(file_dict):
    return os.path.split(file_dict[u'path'])


def getjob(jobid):
    job = ''
    with JOBS_LOCK:
        if 0 <= jobid < len(JOBS):
            job = JOBS[jobid]
    return job


def spool(jobs):
    yield u'['
    connector = u''
    for job in jobs:
        yield connector + dumps(job.getstatus(), indent=4)
        if connector == u'':
            connector = u', '
    yield u']'


def logspooler(job):
    with open(job.logname, b'r') as logfile:
        while True:
            buf = logfile.read(4096)
            if buf:
                yield buf
            else:
                with job.updatelock:
                    if job.status[u'state'] != u'Running':
                        break
                sleep(1)


if __name__ == '__main__':
    # app.debug = True
    APP.run('0.0.0.0')

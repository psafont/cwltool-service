from __future__ import print_function
import os
from functools import wraps
from json import dumps
from threading import Lock
from time import sleep
from future.utils import iteritems

from flask import Flask, Response, request, redirect, abort, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_optional, jwt_required, get_jwt_identity

from cwltoolservice.model.job import Job
from cwltoolservice.model.user import User

APP = Flask(__name__)
APP.config['JWT_PUBLIC_KEY'] = ''  # ???
CORS(APP)
JWT = JWTManager(APP)

JOBS_LOCK = Lock()
JOBS = []

# store which users owns each job (job: user)
USER_OWNS = dict()
# store which jobs are owned by a user (user: [job])
JOBS_OWNED_BY = dict()


# decorator that checks if user has the job
# intended to be used always wrapped in @jwt_otional
def user_is_authorized(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        current_user = get_jwt_identity()
        jobid = kwargs.get('jobid', None)

        if jobid is None:
            return abort(404)

        if current_user != USER_OWNS.get(jobid, None):
            print('user isn\'t authorized!')
            return abort(404)

        return func(*args, **kwargs)

    return wrapper


@APP.route('/run', methods=[u'POST'])
@jwt_optional
def run_workflow():
    path = request.args[u'wf']
    current_user = get_jwt_identity()

    with JOBS_LOCK:
        jobid = len(JOBS)
        job = Job(jobid, path, request.stream.read())
        if current_user:  # non-anonymous user
            USER_OWNS[jobid] = current_user
            JOBS_OWNED_BY[current_user] = JOBS_OWNED_BY.get(current_user, []) + [jobid]
        job.start()
        JOBS.append(job)
    return redirect(u'/jobs/%i' % jobid, code=303)


@APP.route(u'/jobs/<int:jobid>', methods=[u'GET', u'POST'])
@jwt_optional
@user_is_authorized
def job_control(jobid):
    job = getjob(jobid)

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
@jwt_optional
@user_is_authorized
def get_log(jobid):
    job = getjob(jobid)
    return Response(logspooler(job))


@APP.route(u'/jobs/<int:jobid>/output/<string:outputid>', methods=[u'GET'])
@jwt_optional
@user_is_authorized
def get_output(jobid, outputid):
    job = getjob(jobid)

    output = getoutputobj(job.status, outputid)
    if not output:
        return abort(404)

    (path, filename) = getfile(output)
    if not path or not filename:
        return abort(404)

    return send_from_directory(path, filename)


@APP.route(u'/jobs', methods=[u'GET'])
@jwt_required
def get_jobs():
    job_ids = JOBS_OWNED_BY.get(get_jwt_identity(), [])
    jobs = []
    with JOBS_LOCK:
        for job_id in job_ids:
            jobs.append(JOBS[job_id])
    return Response(spool(jobs))


def getoutputobj(status, outputid):
    try:
        return status[u'output'][outputid]
    except KeyError:
        return None


@JWT.user_loader_callback_loader
def user_loader_callback(identity):
    return User(identity)


def getfile(file_dict):
    return os.path.split(file_dict[u'path'])


def getjob(jobid):
    job = None
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

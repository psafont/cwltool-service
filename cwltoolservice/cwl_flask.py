from __future__ import print_function
import os
from functools import wraps
from json import dumps
from threading import Lock
from time import sleep
from future.utils import iteritems

from cryptography.x509 import load_pem_x509_certificate as load_pem
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend

from flask import Flask, Response, request, redirect, abort, send_from_directory, jsonify
from flask_cors import CORS
from aap_client.flask.decorators import jwt_optional, jwt_required, get_user
from aap_client.flask.client import JWTClient

from cwltoolservice.model.job import Job

APP = Flask(__name__, instance_relative_config=True)

CORS(APP)
JWT = JWTClient(APP)

JOBS_LOCK = Lock()
JOBS = []

# store which users owns each job (job: user)
USER_OWNS = dict()
# store which jobs are owned by a user (user: [job])
JOBS_OWNED_BY = dict()


# decorator that checks if the job referred by jobid exists
def job_exists(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        jobid = kwargs.get(u'jobid', None)
        is_a_job = False
        with JOBS_LOCK:
            if 0 <= jobid < len(JOBS):
                is_a_job = True

        if not is_a_job:
            abort(404)
        return func(*args, **kwargs)

    return wrapper


# decorator that checks if user has the job
# intended to be used always wrapped in @jwt_otional
def user_is_authorized(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        current_user = get_user()
        jobid = kwargs.get(u'jobid', None)

        if jobid is None or current_user != USER_OWNS.get(jobid, None):
            return abort(404)

        return func(*args, **kwargs)

    return wrapper


@APP.errorhandler(404)
def page_not_found(e):
    return jsonify(error=404, text=str(e)), 404


@APP.route(u'/run', methods=[u'POST'])
@jwt_optional
def run_workflow():
    path = request.args[u'wf']
    current_user = get_user()

    with JOBS_LOCK:
        jobid = len(JOBS)
        body = request.stream.read()
        job = Job(jobid, path, body)
        JOBS.append(job)

    if current_user:  # non-anonymous user
        USER_OWNS[jobid] = current_user
        JOBS_OWNED_BY[current_user] = JOBS_OWNED_BY.get(current_user, []) + [jobid]
    job.start()
    return redirect(u'/jobs/%i' % jobid, code=303)


@APP.route(u'/jobs/<int:jobid>', methods=[u'GET', u'POST'])
@jwt_optional
@job_exists
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
@job_exists
@user_is_authorized
def get_log(jobid):
    job = getjob(jobid)
    return Response(logspooler(job))


@APP.route(u'/jobs/<int:jobid>/output/<string:outputid>', methods=[u'GET'])
@jwt_optional
@job_exists
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
    job_ids = JOBS_OWNED_BY.get(get_user(), [])
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


def main():
    # hardcoded private key location, that doesn't have a password
    # When a real private key needs to be used use a non-hardcoded
    # password, and do not commit it to the code repository.
    with open('instance/private_key.pem', 'r') as key_file:
        key = load_pem_private_key(key_file.read().encode(),
                                   password=None,
                                   backend=default_backend())
        APP.config[u'JWT_SECRET_KEY'] = key
    # hardcoded certificate location
    with open('instance/public_cert.pem', 'r') as cert_file:
        cert = load_pem(cert_file.read().encode(),
                        default_backend())
        APP.config[u'JWT_PUBLIC_KEY'] = cert.public_key()

    # APP.debug = True
    APP.config[u'JWT_IDENTITY_CLAIM'] = u'sub'
    APP.config[u'JWT_ALGORITHM'] = u'RS256'

    # APP.config.from_object('config')
    # APP.config.from_pyfile('config.py')
    APP.run(u'0.0.0.0')


if __name__ == u'__main__':
    main()

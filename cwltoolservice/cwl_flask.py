from __future__ import print_function
import os

from json import dumps
from future.utils import iteritems

from flask import (
    Flask, Response, request, redirect, abort, send_from_directory, jsonify
)

from flask_cors import CORS

from aap_client.crypto_files import (
    load_public_from_x509, load_private_from_pem
)
from aap_client.flask.client import JWTClient
from aap_client.flask.decorators import jwt_optional, jwt_required, get_user

import cwltoolservice.make_enum_json_serializable  # noqa: F401

from cwltoolservice import JOBS, JOBS_LOCK, USER_OWNS, JOBS_OWNED_BY
from cwltoolservice.decorators import job_exists, user_is_authorized
from cwltoolservice.model.job import Job


def app():
    web_app = Flask(__name__, instance_relative_config=True)

    CORS(web_app)
    JWTClient(web_app)

    # configure
    web_app.config[u'JWT_IDENTITY_CLAIM'] = u'sub'
    web_app.config[u'JWT_ALGORITHM'] = u'RS256'

    web_app.config.from_pyfile('application.cfg')

    private_key_secret = web_app.config[u'PRIVATE_KEY_PASSCODE']
    key = load_private_from_pem(web_app.config[u'PRIVATE_KEY_FILE'],
                                secret=private_key_secret)
    web_app.config[u'JWT_SECRET_KEY'] = key

    public_key = load_public_from_x509(web_app.config[u'X509_FILE'])
    web_app.config[u'JWT_PUBLIC_KEY'] = public_key
    return web_app


APP = app()


# changes location from local filesystem to flask endpoint URL
def url_location(job):
    # replace location so web clients can retrieve any outputs
    for name, output in iteritems(job.output()):
        output[u'location'] = u'/'.join(
            job.url_root()[:-1] + [
                u'jobs', str(job.jobid()),
                u'output', name])


@APP.errorhandler(404)
def page_not_found(error):
    return jsonify(error=404, text=str(error)), 404


@APP.errorhandler(500)
def badaboom(error):
    return jsonify(error=500, text=u'Internal server error, please contact the administrator.'), 500


@APP.route(u'/run', methods=[u'POST'])
@jwt_optional
def run_workflow():
    path = request.args[u'wf']
    current_user = get_user()
    oncompletion = url_location

    with JOBS_LOCK:
        jobid = len(JOBS)
        body = request.stream.read()
        job = Job(jobid, path, body, request.url_root,
                  oncompletion=oncompletion, owner=current_user)
        JOBS.append(job)

    if current_user:  # non-anonymous user
        USER_OWNS[jobid] = current_user
        JOBS_OWNED_BY[current_user] =\
            JOBS_OWNED_BY.get(current_user, []) + [jobid]
    job.start()
    return redirect(u'/jobs/%i' % jobid, code=303)


@APP.route(u'/jobs/<int:jobid>', methods=[u'GET', u'POST'], strict_slashes=False)
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

    return dumps(job.status()), 200, u''


@APP.route(u'/jobs/<int:jobid>/log', methods=[u'GET'])
@jwt_optional
@job_exists
@user_is_authorized
def get_log(jobid):
    job = getjob(jobid)
    return Response(job.logspooler())


@APP.route(u'/jobs/<int:jobid>/output/<string:outputid>', methods=[u'GET'])
@jwt_optional
@job_exists
@user_is_authorized
def get_output(jobid, outputid):
    job = getjob(jobid)

    output = getoutputobj(job.status(), outputid)
    if not output:
        return abort(404)

    (path, filename) = getfile(output)
    if not path or not filename:
        return abort(404)

    return send_from_directory(path, filename)


@APP.route(u'/jobs', methods=[u'GET'], strict_slashes=False)
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
    except (KeyError, TypeError):
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
        yield connector + dumps(job.status())
        if connector == u'':
            connector = u', '
    yield u']'


def main():
    # APP.debug = True
    APP.run(u'0.0.0.0')


if __name__ == u'__main__':
    main()

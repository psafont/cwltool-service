from __future__ import print_function
import os

import json
from future.utils import iteritems

from flask import (
    Response, request, redirect, abort, send_from_directory, jsonify
)

from aap_client.flask.decorators import jwt_optional, jwt_required, get_user
from sqlalchemy.exc import SQLAlchemyError

import workflow_service.make_enum_json_serializable  # pylint: disable=W0611

from workflow_service import app, RUNNER_FOR

# We need to initialize the database engine before importing the models and
# its dependencies because what these depend on it being ready to go.
# We cannot have the database ready at the beginning because the URL to
# establish the connection is gathered by Flask
APP = app()

from workflow_service.database import DB_SESSION # pylint: disable=C0413
from workflow_service.models import Job, State, update_job # pylint: disable=C0413
from workflow_service.decorators import user_owns_job # pylint: disable=C0413
from workflow_service.job_runner import JobRunner # pylint: disable=C0413


# changes location from local filesystem to flask endpoint URL
def url_location(url_root):
    def new_locations(job_runner, jobid):
        # replace locations in the outputs so web clients can retrieve all
        # the outputs
        output = json.loads(job_runner.output) if job_runner.output else {}
        return change_all_locations(
            output,
            url_root[:-1] + u'/jobs/' + jobid + u'/output')
    return new_locations


def change_all_locations(obj, url_name):
    if isinstance(obj, list):
        for o_name, output in enumerate(obj):
            change_all_locations(output, url_name + u'/' + str(o_name))
    elif isinstance(obj, dict):
        if 'location' not in obj:
            for o_name, output in iteritems(obj):
                change_all_locations(output, url_name + u'/' + o_name)
        else:
            obj[u'location'] = url_name
    else:
        APP.logger.warning(
            u'Couldn\'t process output "%s" to change the locations', url_name)
    return obj


@APP.errorhandler(404)
def page_not_found(error):
    return jsonify(error=404, text=str(error)), 404


@APP.errorhandler(500)
def internal_error_handler(error):
    APP.logger.error(error)
    return (
        jsonify(
            error=500,
            text=u'Internal server error, please contact the administrator.'),
        500
    )


@APP.teardown_appcontext
def shutdown_session(exception=None):  # pylint: disable=unused-argument
    DB_SESSION.remove()


@APP.route(u'/health', methods=[u'GET'])
def health_report():
    return Response('It\'s alive!')


@APP.route(u'/run', methods=[u'POST'])
@jwt_optional
def run_workflow():
    path = request.args[u'wf']
    current_user = get_user()
    body = request.stream.read()
    url_root = request.url_root

    session = DB_SESSION()
    try:
        job = Job(path, body, request.url_root, current_user)
        session.add(job)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        return internal_error_handler(
            u'Internal error: could not access persistence layer. ' +
            u'Please try again. If the error persists contact an admin.'
        )

    def on_finishing(job_runner):
        state = State.Error
        output = None
        try:
            output = url_location(url_root)(job_runner, str(job.id))
            state = job_runner.state
        except Exception as err:  # pylint: disable=broad-except
            APP.logger.error(err)

        try:
            update_job(APP, job, state, output)
        except SQLAlchemyError as err:
            APP.logger.error(err)

    runner = JobRunner(path, body, job.id, on_finishing)
    RUNNER_FOR[job.id] = runner
    runner.start()

    return redirect(u'/jobs/{}'.format(job.id), code=303)


@APP.route(u'/jobs/<uuid:jobid>',
           methods=[u'GET'],
           strict_slashes=False)
@jwt_optional
@user_owns_job
def job_control(jobid):
    job = job_from_id(jobid)
    return json.dumps(job.status()), 200, u''


@APP.route(u'/jobs/<uuid:jobid>/log', methods=[u'GET'])
@jwt_optional
@user_owns_job
def get_log(jobid):
    return Response(RUNNER_FOR[jobid].logspooler(), mimetype='text/event-stream')


@APP.route(u'/jobs/<uuid:jobid>/output/<path:outputid>', methods=[u'GET'])
@jwt_optional
@user_owns_job
def get_output(jobid, outputid):
    job = job_from_id(jobid)

    output = getoutputobj(job.status, outputid)
    if not output or not isfile(output):
        return abort(404)

    (path, filename), wf_filename = getfile(output)
    if not path or not filename:
        return abort(404)

    return send_from_directory(path, filename, attachment_filename=wf_filename)


@APP.route(u'/jobs', methods=[u'GET'], strict_slashes=False)
@jwt_required
def get_jobs():
    jobs = jobs_from_owner(get_user())
    return Response(spool(jobs), mimetype='application/json')


def getoutputobj(status, outputid):
    path = outputid.split(u'/')
    try:
        ref = status[u'output']
        for key in path:
            if isinstance(ref, list):
                key = int(key)
            ref = ref[key]

        return ref
    except (KeyError, TypeError, ValueError, IndexError) as err:
        APP.logger.info(
            u'Couldn\'t retrieve output "%s" because %s', outputid, str(err))
        return None


def isfile(obj):
    return isinstance(obj, dict) and u'path' in obj and u'basename' in obj


def getfile(file_dict):
    return os.path.split(file_dict[u'path']), file_dict[u'basename']


def job_from_id(jobid):
    return _filter_jobs(Job.id, jobid).first()


def jobs_from_owner(owner):
    return _filter_jobs(Job.owner, owner)


def _filter_jobs(key, value):
    jobs = []

    try:
        session = DB_SESSION()
        jobs = session.query(Job).filter(key == value)
    except SQLAlchemyError:
        abort(500)

    return jobs


def spool(jobs):
    yield u'['
    connector = u''
    for job in jobs:
        yield connector + json.dumps(job.status())
        if connector == u'':
            connector = u', '
    yield u']'


def main():
    # APP.debug = True
    APP.run(u'0.0.0.0')


if __name__ == u'__main__':
    main()

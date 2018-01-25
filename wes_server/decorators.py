from functools import wraps

from flask import abort
from aap_client.flask.decorators import get_user

from wes_server import JOBS_LOCK, JOBS, USER_OWNS


def job_exists(func):
    # decorator that checks if the job referred by jobid exists
    @wraps(func)
    def wrapper(*args, **kwargs):
        jobid = kwargs.get(u'jobid', None)

        with JOBS_LOCK:
            if jobid not in JOBS:
                abort(404)

        return func(*args, **kwargs)

    return wrapper


def user_is_authorized(func):
    # decorator that checks if user has the job
    # intended to be used always wrapped in @jwt_optional
    @wraps(func)
    def wrapper(*args, **kwargs):
        current_user = get_user()
        jobid = kwargs.get(u'jobid', None)

        with JOBS_LOCK:
            if jobid is None or current_user != USER_OWNS.get(jobid, None):
                return abort(404)

        return func(*args, **kwargs)

    return wrapper

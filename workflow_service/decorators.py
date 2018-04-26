from functools import wraps
from uuid import UUID

from werkzeug.routing import BaseConverter
from flask import abort
from aap_client.flask.decorators import get_user
from sqlalchemy.exc import OperationalError

from workflow_service.database import DB_SESSION
from workflow_service.models import Job


def user_owns_job(func):
    # decorator that checks if user owns the job
    # intended to be used always wrapped by @jwt_optional/jwt_required
    @wraps(func)
    def wrapper(*args, **kwargs):
        current_user = get_user()
        jobid = kwargs.get(u'jobid', None)

        if jobid is None:
            return abort(404)

        try:
            session = DB_SESSION()

            job = session.query(Job).filter(
                Job.id == jobid, Job.owner == current_user
            ).first()
        except OperationalError:
            return abort(500)

        if not job:
            return abort(404)

        return func(*args, **kwargs)

    return wrapper


class UUIDConverter(BaseConverter):
    def to_python(self, value):
        try:
            return UUID(value)
        except ValueError:
            abort(404)

    def to_url(self, value):
        return str(value)

from __future__ import print_function
import enum
from uuid import uuid4
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy import Column, DateTime, Enum, String, UnicodeText, func
from sqlalchemy_utils import JSONType, UUIDType

from workflow_service.database import BASE, DB_SESSION


@enum.unique  # pylint: disable=too-few-public-methods
class State(enum.Enum):
    Running = u'Running'
    Complete = u'Complete'
    Paused = u'Paused'
    Error = u'Error'
    Cancelled = u'Cancelled'


# pylint: disable=bad-whitespace
class Job(BASE):  # pylint: disable=too-few-public-methods
    __tablename__ = 'jobs'
    id            = Column(UUIDType(native=True), primary_key=True, default=uuid4)
    input_json    = Column(JSONType)
    workflow      = Column(UnicodeText)
    output        = Column(JSONType)
    state         = Column(Enum(State), default=State.Running)
    start_time    = Column(DateTime, server_default=func.now())
    state_time    = Column(DateTime, onupdate=func.now())
    owner         = Column(String(50))
    run_by_host   = Column(String(50))

    def __init__(self, workflow, input_json, hostname, owner=None):
        self.input_json = input_json
        self.workflow = workflow
        self.owner = owner
        self.run_by_host = hostname

    def status(self):
        status = {
            u'id': u'/'.join([self.run_by_host[:-1], u'jobs', str(self.id)]),
            u'log': u'/'.join([self.run_by_host[:-1], u'jobs', str(self.id), u'log']),
            u'run': self.workflow,
            u'state': self.state,
            u'input': self.input_json,
            u'output': self.output
        }

        return status


def update_job(job, state, output):
    """
    Meant to run at the end of asynchronous tasks, in a separate thread,
    which is why we can remove the per-thread db session
    """
    try:
        session = DB_SESSION()
        # update job in db
        job = session.merge(job)
        job.state = state
        job.output = output
        session.commit()
    except SQLAlchemyError:
        if session:
            session.rollback()
    finally:
        DB_SESSION.remove()

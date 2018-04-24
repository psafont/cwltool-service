from __future__ import print_function
import enum
from uuid import uuid4

import json

from sqlalchemy import Column, DateTime, Enum, String, UnicodeText, func
from sqlalchemy_utils import JSONType, UUIDType

from workflow_service.database import BASE


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
    input_obj     = Column(JSONType)
    workflow      = Column(UnicodeText)
    output        = Column(JSONType)
    state         = Column(Enum(State), default=State.Running)
    start_time    = Column(DateTime, server_default=func.now())
    state_time    = Column(DateTime, onupdate=func.now())
    owner         = Column(String(50))
    run_by_host   = Column(String(50))

    def __init__(self, workflow, input_obj, hostname, owner=None):
        self.input_obj = input_obj
        self.workflow = workflow
        self.owner = owner
        self.run_by_host = hostname

    def status(self):
        try:
            input_json = json.loads(self.input_obj)
        except (ValueError, TypeError):
            input_json = None

        status = {
            u'id': u'/'.join([self.run_by_host[:-1], u'jobs', str(self.id)]),
            u'log': u'/'.join([self.run_by_host[:-1], u'jobs', str(self.id), u'log']),
            u'run': self.workflow,
            u'state': self.state,
            u'input': input_json,
            u'output': self.output
        }

        return status

import enum

from sqlalchemy import Column, DateTime, Enum, String, UnicodeText
from sqlalchemy_utils import UUIDType

from workflow_service.database import BASE


@enum.unique  # pylint: disable=too-few-public-methods
class State(enum.Enum):
    Running = u'Running'
    Complete = u'Complete'
    Paused = u'Paused'
    Error = u'Error'
    Canceled = u'Cancelled'


# pylint: disable=bad-whitespace
class Job(BASE):  # pylint: disable=too-few-public-methods
    __tablename__ = 'jobs'
    id            = Column(UUIDType(), primary_key=True)
    input         = Column(UnicodeText)
    workflow      = Column(UnicodeText)
    output        = Column(UnicodeText)
    state         = Column(Enum(State))
    creation_time = Column(DateTime)
    end_time      = Column(DateTime)
    user_id       = Column(String(50))
    run_by_host   = Column(String(50))

    def __repr__(self):
        return '<User %r>' % (self.id)

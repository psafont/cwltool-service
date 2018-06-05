from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

ENGINE = None
DB_SESSION = None
BASE = None

# pylint: disable=global-statement
def init_db_engine(db_uri):
    global ENGINE
    ENGINE = create_engine(db_uri, convert_unicode=True, echo=False)

    global DB_SESSION
    DB_SESSION = scoped_session(sessionmaker(bind=ENGINE))

    global BASE
    BASE = declarative_base()
    BASE.query = DB_SESSION.query_property()

def init_db_models():
    BASE.metadata.create_all(bind=ENGINE)

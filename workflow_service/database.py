from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

DB_URI = 'sqlite:///:memory:'
ENGINE = create_engine(DB_URI, convert_unicode=True, echo=False)
DB_SESSION = scoped_session(sessionmaker(bind=ENGINE))
BASE = declarative_base()
BASE.query = DB_SESSION.query_property()


def init_db():
    # create tables
    BASE.metadata.create_all(bind=ENGINE)

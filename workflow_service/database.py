from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

ENGINE = create_engine('sqlite:///:memory:', convert_unicode=True, echo=True)
DB_SESSION = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=ENGINE))
BASE = declarative_base()
BASE.query = DB_SESSION.query_property()


def init_db():
    BASE.metadata.create_all(bind=ENGINE)

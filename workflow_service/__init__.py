import logging

from flask import Flask
from flask_cors import CORS

from aap_client.flask.client import JWTClient
from aap_client.crypto_files import load_public_from_x509
from workflow_service.database import init_db_engine, init_db_models

# jobid -> runner
RUNNER_FOR = dict()


def init_loggers(web_app):
    # flask is naughty and sets up default handlers
    # some spanking is in order
    del web_app.logger.handlers[:]

    # log errors to stderr
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    web_app.logger.addHandler(handler)
    web_app.logger.setLevel(logging.WARNING)


def init_db(db_uri):
    init_db_engine(db_uri)
    # import all db models before initialising the database
    # so they are registered properly on the metadata.
    from workflow_service import models  # pylint: disable=unused-variable
    init_db_models()


def init_extensions(web_app):
    CORS(web_app)
    JWTClient(web_app)


def configure_app(web_app, config):
    web_app.config[u'JWT_IDENTITY_CLAIM'] = u'sub'
    web_app.config[u'JWT_ALGORITHM'] = u'RS256'

    web_app.config.from_pyfile(config)

    init_db(web_app.config[u'SQLALCHEMY_DATABASE_URI'])

    # set up new url mapper to load uuids
    from workflow_service.decorators import UUIDConverter
    web_app.url_map.converters['uuid'] = UUIDConverter

    public_key = load_public_from_x509(web_app.config[u'X509_FILE'])
    web_app.config[u'JWT_PUBLIC_KEY'] = public_key


def app(config='application.cfg'):
    web_app = Flask(__name__, instance_relative_config=True)

    init_loggers(web_app)
    configure_app(web_app, config)

    init_extensions(web_app)

    return web_app

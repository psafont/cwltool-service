from threading import Lock
import logging

from flask import Flask
from flask_cors import CORS

from aap_client.flask.client import JWTClient
from aap_client.crypto_files import (
    load_public_from_x509, load_private_from_pem
)

# from workflow_service.database import init_db
# import all db models before initialising the database
# so they are registered properly on the metadata.
import workflow_service.models  # pylint: disable=unused-variable

JOBS_LOCK = Lock()
JOBS = dict()

# store which users owns each job (job: user)
USER_OWNS = dict()
# store which jobs are owned by a user (user: [job])
JOBS_OWNED_BY = dict()

def app():
    web_app = Flask(__name__, instance_relative_config=True)

    CORS(web_app)
    JWTClient(web_app)

    # flask is naughty and sets up default handlers
    # some spanking is in order
    del web_app.logger.handlers[:]

    # log errors to stderr
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    web_app.logger.addHandler(handler)
    web_app.logger.setLevel(logging.ERROR)

    # configure
    web_app.config[u'JWT_IDENTITY_CLAIM'] = u'sub'
    web_app.config[u'JWT_ALGORITHM'] = u'RS256'

    web_app.config.from_pyfile('application.cfg')

    private_key_secret = web_app.config[u'PRIVATE_KEY_PASSCODE']
    key = load_private_from_pem(web_app.config[u'PRIVATE_KEY_FILE'],
                                secret=private_key_secret)
    web_app.config[u'JWT_SECRET_KEY'] = key

    public_key = load_public_from_x509(web_app.config[u'X509_FILE'])
    web_app.config[u'JWT_PUBLIC_KEY'] = public_key
    return web_app

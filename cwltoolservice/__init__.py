from threading import Lock

from flask import Flask
from flask_cors import CORS

from aap_client.crypto_files import load_public_from_x509
from aap_client.crypto_files import load_private_from_pem
from aap_client.flask.client import JWTClient

JOBS_LOCK = Lock()
JOBS = []

# store which users owns each job (job: user)
USER_OWNS = dict()
# store which jobs are owned by a user (user: [job])
JOBS_OWNED_BY = dict()


def app():
    app = Flask(__name__, instance_relative_config=True)

    CORS(app)
    JWTClient(app)

    # configure
    app.config[u'JWT_IDENTITY_CLAIM'] = u'sub'
    app.config[u'JWT_ALGORITHM'] = u'RS256'

    app.config.from_pyfile('application.cfg')

    private_key_secret = app.config[u'PRIVATE_KEY_PASSCODE']
    key = load_private_from_pem(app.config[u'PRIVATE_KEY_FILE'],
                                secret=private_key_secret)
    app.config[u'JWT_SECRET_KEY'] = key

    public_key = load_public_from_x509(app.config[u'X509_FILE'])
    app.config[u'JWT_PUBLIC_KEY'] = public_key
    return app


APP = app()

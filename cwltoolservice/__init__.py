from threading import Lock

from flask import Flask
from flask_cors import CORS

from aap_client.crypto_files import load_public_from_x509
from aap_client.crypto_files import load_private_from_pem
from aap_client.flask.client import JWTClient

APP = Flask(__name__, instance_relative_config=True)

CORS(APP)
JWT = JWTClient(APP)

JOBS_LOCK = Lock()
JOBS = []

# store which users owns each job (job: user)
USER_OWNS = dict()
# store which jobs are owned by a user (user: [job])
JOBS_OWNED_BY = dict()

# configure
APP.config[u'JWT_IDENTITY_CLAIM'] = u'sub'
APP.config[u'JWT_ALGORITHM'] = u'RS256'

APP.config.from_pyfile('application.cfg')

private_key_secret = APP.config[u'PRIVATE_KEY_PASSCODE']
key = load_private_from_pem(APP.config[u'PRIVATE_KEY_FILE'],
                            secret=private_key_secret)
APP.config[u'JWT_SECRET_KEY'] = key

public_key = load_public_from_x509(APP.config[u'X509_FILE'])
APP.config[u'JWT_PUBLIC_KEY'] = public_key

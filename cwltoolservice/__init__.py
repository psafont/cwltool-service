from threading import Lock

from aap_client.flask.client import JWTClient
from flask import Flask
from flask_cors import CORS

APP = Flask(__name__, instance_relative_config=True)

CORS(APP)
JWT = JWTClient(APP)

JOBS_LOCK = Lock()
JOBS = []

# store which users owns each job (job: user)
USER_OWNS = dict()
# store which jobs are owned by a user (user: [job])
JOBS_OWNED_BY = dict()

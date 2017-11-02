from threading import Lock

JOBS_LOCK = Lock()
JOBS = []

# store which users owns each job (job: user)
USER_OWNS = dict()
# store which jobs are owned by a user (user: [job])
JOBS_OWNED_BY = dict()

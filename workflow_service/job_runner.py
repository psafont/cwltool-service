from sys import prefix
import os
from signal import SIGQUIT, SIGTSTP, SIGCONT
from subprocess import Popen, PIPE
import tempfile
from threading import Thread, Lock
from time import sleep

import json
from uuid import uuid4

import yaml

from workflow_service.models import State

def makedirs(path):
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise


class JobRunner(Thread):  # pylint: disable=R0902
    # pylint: disable=R0913
    def __init__(self, wf_path, inputobj, url_root,
                 oncompletion=lambda *args, **kwargs: None, owner=None):
        super(JobRunner, self).__init__()

        try:
            input_json = json.loads(inputobj)
        except ValueError:
            input_json = None

        self._uuid = uuid4()
        self._inputobj = inputobj
        self._oncompletion = oncompletion
        self._owner = owner

        self.outdir = os.path.join(
            tempfile.gettempdir(), str(self._uuid), 'out')
        makedirs(self.outdir)
        loghandle, self.logname =\
            tempfile.mkstemp(dir=os.path.split(self.outdir)[0])

        self._job_status = {
            u'id': u'{}jobs/{}'.format(url_root, self._uuid),
            u'log': u'{}jobs/{}/log'.format(url_root, self._uuid),
            u'run': wf_path,
            u'state': State.Running,
            u'input': input_json,
            u'output': None
        }

        self._updatelock = Lock()

        with self._updatelock:
            self._proc = Popen([prefix + u'/bin/python',
                                u'-m',
                                u'cwltool',
                                u'--user-space-docker-cmd=udocker',
                                u'--leave-outputs', wf_path, u'-'],
                               stdin=PIPE,
                               stdout=PIPE,
                               stderr=loghandle,
                               close_fds=True,
                               cwd=self.outdir)

    def run(self):
        stdoutdata, _ = self._proc.communicate(self._inputobj)
        if self._proc.returncode == 0:
            outobj = yaml.load(stdoutdata)
            with self._updatelock:
                self._job_status[u'state'] = State.Complete
                self._job_status[u'output'] = outobj

                # capture output files here and upload to owncloud
                self._oncompletion(self)
        else:
            with self._updatelock:
                self._job_status[u'state'] = State.Error

    def _status(self):
        return self._job_status

    def _state(self):
        return self._job_status[u'state']

    def status(self):
        with self._updatelock:
            return self._status()

    def output(self):
        return self._job_status[u'output']

    def jobid(self):
        return str(self._uuid)

    def owner(self):
        return self._owner

    def logspooler(self):
        with open(self.logname, 'r') as logfile:
            chunk = logfile.readline(4096)
            try:
                while chunk:
                    yield chunk
                    chunk = logfile.readline(4096)

                while self._state() == State.Running:
                    if chunk:
                        yield chunk
                    else:
                        sleep(1)
                    chunk = logfile.readline(4096)
            except IOError:
                pass

    def cancel(self):
        with self._updatelock:
            if self._state() == State.Running:
                self._proc.send_signal(SIGQUIT)
                self._job_status[u'state'] = State.Canceled

    def pause(self):
        with self._updatelock:
            if self._state() == State.Running:
                self._proc.send_signal(SIGTSTP)
                self._job_status[u'state'] = State.Paused

    def resume(self):
        with self._updatelock:
            if self._state() == State.Paused:
                self._proc.send_signal(SIGCONT)
                self._job_status[u'state'] = State.Running

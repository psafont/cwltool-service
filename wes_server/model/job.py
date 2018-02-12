from sys import prefix
from signal import SIGQUIT, SIGTSTP, SIGCONT
from subprocess import Popen, PIPE
from tempfile import mkstemp, mkdtemp
from threading import Thread, Lock
from time import sleep

import json
from enum import Enum, unique

import yaml


# pylint: disable=R0902
class Job(Thread):
    @unique  # pylint: disable=R0903
    class State(Enum):
        Running = u'Running'
        Complete = u'Complete'
        Paused = u'Paused'
        Error = u'Error'
        Canceled = u'Cancelled'

    # pylint: disable=R0913
    def __init__(self, wf_path, inputobj, url_root,
                 oncompletion=lambda *args, **kwargs: None, owner=None):
        super(Job, self).__init__()

        try:
            input_json = json.loads(inputobj)
        except ValueError:
            input_json = None

        self._inputobj = inputobj
        self._oncompletion = oncompletion
        self._owner = owner

        loghandle, self.logname = mkstemp()
        self.outdir = mkdtemp(prefix=u'wes')

        self._job_status = {
            u'id': u'{}jobs/{}'.format(url_root, self.jobid()),
            u'log': u'{}jobs/{}/log'.format(url_root, self.jobid()),
            u'run': wf_path,
            u'state': self.State.Running,
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
                self._job_status[u'state'] = self.State.Complete
                self._job_status[u'output'] = outobj

                # capture output files here and upload to owncloud
                self._oncompletion(self)
        else:
            with self._updatelock:
                self._job_status[u'state'] = self.State.Error

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
        return self.outdir.split('/')[-1][3:]

    def owner(self):
        return self._owner

    def logspooler(self):
        with open(self.logname, 'r') as logfile:
            chunk = logfile.readline(4096)
            try:
                while chunk:
                    yield chunk
                    chunk = logfile.readline(4096)

                while self._state() == self.State.Running:
                    if chunk:
                        yield chunk
                    else:
                        sleep(1)
                    chunk = logfile.readline(4096)
            except IOError:
                pass

    def cancel(self):
        with self._updatelock:
            if self._state() == self.State.Running:
                self._proc.send_signal(SIGQUIT)
                self._job_statu[u'state'] = self.State.Canceled

    def pause(self):
        with self._updatelock:
            if self._state() == self.State.Running:
                self._proc.send_signal(SIGTSTP)
                self._job_status[u'state'] = self.State.Paused

    def resume(self):
        with self._updatelock:
            if self._state() == self.State.Paused:
                self._proc.send_signal(SIGCONT)
                self._job_status[u'state'] = self.State.Running

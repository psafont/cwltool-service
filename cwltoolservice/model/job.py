from signal import SIGQUIT, SIGTSTP, SIGCONT
from subprocess import Popen, PIPE
from tempfile import mkstemp, mkdtemp
from threading import Thread, Lock

import json
from enum import Enum, unique

import yaml
from future.utils import iteritems


class Job(Thread):
    @unique
    class State(Enum):
        Running = "Running"
        Complete = "Complete"
        Paused = "Paused"
        Error = "Error"
        Canceled = "Cancelled"

    def __init__(self, jobid, path, inputobj, url_root, oncompletion=lambda: None):
        super(Job, self).__init__()
        self._jobid = jobid
        self._path = path
        self._inputobj = inputobj
        self.oncompletion = oncompletion
        self._url_root = url_root

        self._state = self.State.Running
        self._output = None

        self._updatelock = Lock()

        with self._updatelock:
            loghandle, self.logname = mkstemp()
            self.outdir = mkdtemp()
            self.proc = Popen(['cwl-runner',
                               '--leave-outputs', self._path, '-'],
                              stdin=PIPE,
                              stdout=PIPE,
                              stderr=loghandle,
                              close_fds=True,
                              cwd=self.outdir)

    def _status(self):
        status = {
            'id': '%sjobs/%i' % (self._url_root, self._jobid),
            'log': '%sjobs/%i/log' % (self._url_root, self._jobid),
            'run': self._path,
            'state': self._state,
            'input': json.loads(self._inputobj),
            'output': self._output
        }
        return status

    def run(self):
        stdoutdata, _ = self.proc.communicate(self._inputobj)
        if self.proc.returncode == 0:
            outobj = yaml.load(stdoutdata)
            with self._updatelock:
                self._state = self.State.Complete
                self._output = outobj

                # replace location so web clients can retrieve any outputs
                for name, output in iteritems(self._output):
                    output[u'location'] = u'/'.join([self._url_root,
                                                     u'jobs', str(self._jobid), u'output', name])

                # capture output files here and upload to owncloud
                self.oncompletion()
        else:
            with self._updatelock:
                self._state = self.State.Error

    def status(self):
        with self._updatelock:
            return self._status()

    def cancel(self):
        with self._updatelock:
            if self._state == self.State.Running:
                self.proc.send_signal(SIGQUIT)
                self._state = self.State.Canceled

    def pause(self):
        with self._updatelock:
            if self._state == self.State.Running:
                self.proc.send_signal(SIGTSTP)
                self._state = self.State.Paused

    def resume(self):
        with self._updatelock:
            if self._state == self.State.Paused:
                self.proc.send_signal(SIGCONT)
                self._state = self.State.Running

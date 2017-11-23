from sys import prefix
from signal import SIGQUIT, SIGTSTP, SIGCONT
from subprocess import Popen, PIPE
from tempfile import mkstemp, mkdtemp
from threading import Thread, Lock
from time import sleep

import json
from enum import Enum, unique

import yaml


class Job(Thread):
    @unique
    class State(Enum):
        Running = u"Running"
        Complete = u"Complete"
        Paused = u"Paused"
        Error = u"Error"
        Canceled = u"Cancelled"

    def __init__(self, jobid, path, inputobj, url_root,
                 oncompletion=lambda *args, **kwargs: None, owner=None):
        super(Job, self).__init__()
        self._jobid = jobid
        self._path = path
        self._inputobj = inputobj
        self.oncompletion = oncompletion
        self._url_root = url_root
        self._owner = owner

        self._state = self.State.Running
        self._output = None

        self._updatelock = Lock()

        with self._updatelock:
            loghandle, self.logname = mkstemp()
            self.outdir = mkdtemp()
            self.proc = Popen([prefix + u'/bin/python',
                               u'-m',
                               u'cwltool',
                               u'--user-space-docker-cmd=udocker',
                               u'--leave-outputs', self._path, u'-'],
                              stdin=PIPE,
                              stdout=PIPE,
                              stderr=loghandle,
                              close_fds=True,
                              cwd=self.outdir)

    def run(self):
        stdoutdata, _ = self.proc.communicate(self._inputobj)
        if self.proc.returncode == 0:
            outobj = yaml.load(stdoutdata)
            with self._updatelock:
                self._state = self.State.Complete
                self._output = outobj

                # capture output files here and upload to owncloud
                self.oncompletion(self)
        else:
            with self._updatelock:
                self._state = self.State.Error

    def _status(self):
        inputobj = self._inputobj
        try:
            inputobj = json.loads(self._inputobj)
        except ValueError:
            pass

        status = {
            u'id': u'%sjobs/%i' % (self._url_root, self._jobid),
            u'log': u'%sjobs/%i/log' % (self._url_root, self._jobid),
            u'run': self._path,
            u'state': self._state,
            u'input': inputobj,
            u'output': self._output
        }
        return status

    def status(self):
        with self._updatelock:
            return self._status()

    def output(self):
        return self._output

    def jobid(self):
        return self._jobid

    def url_root(self):
        return self._url_root

    def owner(self):
        return self._owner

    def logspooler(self):
        with open(self.logname, 'r') as logfile:
            while True:
                buf = logfile.read(4096)
                if buf:
                    yield buf
                else:
                    if self.status()[u'state'] != u'Running':
                        break
                    sleep(1)

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

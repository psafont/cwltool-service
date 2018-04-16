from sys import prefix
import os
from signal import SIGQUIT, SIGTSTP, SIGCONT
from subprocess import Popen, PIPE
import tempfile
from threading import Thread, Lock
from time import sleep

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
    """
    Args:
        onsuccess: action that is performed when any job finishes
                   successfully. Its signature must be in the form of
                   f(JobRunner) -> None
        onfailure: action that is performed when any job fails.
                   Its signature must be in the form of
                   f(JobRunner) -> None
    """
    def __init__(self, wf_path, input_obj, uuid,
                 onsuccess=lambda *args, **kwargs: None,
                 onfailure=lambda *args, **kwargs: None,
                 owner=None):
        super(JobRunner, self).__init__()

        self._inputobj = input_obj
        self._onsuccess = onsuccess
        self._onfailure = onfailure
        self._owner = owner
        self.uuid = uuid

        self.state = State.Running
        self.output = None

        self.outdir = os.path.join(
            tempfile.gettempdir(), str(self.uuid), 'out')
        makedirs(self.outdir)
        loghandle, self.logname =\
            tempfile.mkstemp(dir=os.path.split(self.outdir)[0])

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
                self.state = State.Complete
                self.output = outobj

                self._onsuccess(self)
        else:
            with self._updatelock:
                self.state = State.Error
                self._onfailure(self)

    def logspooler(self):
        with open(self.logname, 'r') as logfile:
            chunk = logfile.readline(4096)
            try:
                while chunk:
                    yield chunk
                    chunk = logfile.readline(4096)

                while self.state == State.Running:
                    if chunk:
                        yield chunk
                    else:
                        sleep(1)
                    chunk = logfile.readline(4096)
            except IOError:
                pass

    def cancel(self):
        with self._updatelock:
            if self.state == State.Running:
                self._proc.send_signal(SIGQUIT)
                self.state = State.Canceled

    def pause(self):
        with self._updatelock:
            if self.state == State.Running:
                self._proc.send_signal(SIGTSTP)
                self.state = State.Paused

    def resume(self):
        with self._updatelock:
            if self.state == State.Paused:
                self._proc.send_signal(SIGCONT)
                self.state = State.Running

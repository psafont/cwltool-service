
from signal import SIGQUIT, SIGTSTP, SIGCONT
from subprocess import Popen, PIPE
from tempfile import mkstemp, mkdtemp
from threading import Thread, Lock

import json
from enum import Enum, unique

from flask import request

import yaml


class Job(Thread):
    @unique
    class State(Enum):
        Running = 1
        Complete = 2
        Paused = 3
        Error = 4
        Canceled = 5

    # pylint: disable=too-many-instance-attributes
    def __init__(self, jobid, path, inputobj):
        super(Job, self).__init__()
        self.jobid = jobid
        self.path = path
        self.inputobj = inputobj
        self.status = {
            'id': '%sjobs/%i' % (request.url_root, self.jobid),
            'log': '%sjobs/%i/log' % (request.url_root, self.jobid),
            'run': self.path,
            'state': 'Running',
            'input': json.loads(self.inputobj),
            'output': None
        }

        self.stdoutdata = self.stderrdata = None
        self.updatelock = Lock()

        with self.updatelock:
            loghandle, self.logname = mkstemp()
            self.outdir = mkdtemp()
            self.proc = Popen(['cwl-runner', '--leave-outputs', self.path, '-'],
                              stdin=PIPE,
                              stdout=PIPE,
                              stderr=loghandle,
                              close_fds=True,
                              cwd=self.outdir)

    def run(self):
        self.stdoutdata, self.stderrdata = self.proc.communicate(self.inputobj)
        if self.proc.returncode == 0:
            outobj = yaml.load(self.stdoutdata)
            with self.updatelock:
                self.status['state'] = 'Complete'
                self.status['output'] = outobj
        else:
            with self.updatelock:
                self.status['state'] = 'Error'

    def getstatus(self):
        with self.updatelock:
            return self.status.copy()

    def cancel(self):
        if self.status['state'] == 'Running':
            self.proc.send_signal(SIGQUIT)
            with self.updatelock:
                self.status['state'] = 'Canceled'

    def pause(self):
        if self.status['state'] == 'Running':
            self.proc.send_signal(SIGTSTP)
            with self.updatelock:
                self.status['state'] = 'Paused'

    def resume(self):
        if self.status['state'] == 'Paused':
            self.proc.send_signal(SIGCONT)
            with self.updatelock:
                self.status['state'] = 'Running'

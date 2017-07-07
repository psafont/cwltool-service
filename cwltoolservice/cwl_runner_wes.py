import subprocess
import uuid
import os

import json

import connexion
import connexion.utils as utils
from connexion.resolver import Resolver


class Workflow(object):
    def __init__(self, workflow_id):
        super(Workflow, self).__init__()
        self.workflow_id = workflow_id
        self.workdir = os.path.abspath(self.workflow_id)

    def run(self, path, inputobj):
        path = os.path.abspath(path)
        os.mkdir(self.workdir)
        outdir = os.path.join(self.workdir, u'outdir')
        os.mkdir(outdir)
        with open(os.path.join(self.workdir, u'cwl.input.json'), b'w') as inputtemp:
            json.dump(inputobj, inputtemp)
        with open(os.path.join(self.workdir, u'workflow_url'), b'w') as workflow_file:
            workflow_file.write(path)
        output = open(os.path.join(self.workdir, u'cwl.output.json'), b'w')
        stderr = open(os.path.join(self.workdir, u'stderr'), b'w')

        proc = subprocess.Popen([u'cwl-runner', path, inputtemp.name],
                                stdout=output,
                                stderr=stderr,
                                close_fds=True,
                                cwd=outdir)
        output.close()
        stderr.close()
        with open(os.path.join(self.workdir, u'pid'), b'w') as pid:
            pid.write(str(proc.pid))

        return self.getstatus()

    def getstate(self):
        state = u'Running'
        exit_code = -1

        exc = os.path.join(self.workdir, u'exit_code')
        if os.path.exists(exc):
            with open(exc) as exit_file:
                exit_code = int(exit_file.read())
        else:
            with open(os.path.join(self.workdir, u'pid'), b'r') as pid:
                pid = int(pid.read())
            (_pid, exit_status) = os.waitpid(pid, os.WNOHANG)
            if _pid != 0:
                exit_code = exit_status >> 8
                with open(exc, b'w') as exit_file:
                    exit_file.write(str(exit_code))
                os.unlink(os.path.join(self.workdir, u'pid'))

        if exit_code == 0:
            state = u'Complete'
        elif exit_code != -1:
            state = u'Failed'

        return (state, exit_code)

    def getstatus(self):
        state, _ = self.getstate()

        with open(os.path.join(self.workdir, u'cwl.input.json'), b'r') as inputtemp:
            inputobj = json.load(inputtemp)
        with open(os.path.join(self.workdir, u'workflow_url'), b'r') as workflow_file:
            workflow_url = workflow_file.read()

        outputobj = {}
        if state == u'Complete':
            with open(os.path.join(self.workdir, u'cwl.output.json'), b'r') as outputtemp:
                outputobj = json.load(outputtemp)

        return {
            u'workflow_ID': self.workflow_id,
            u'workflow_url': workflow_url,
            u'input': inputobj,
            u'output': outputobj,
            u'state': state
        }

    def getlog(self):
        _, exit_code = self.getstate()

        with open(os.path.join(self.workdir, u'stderr'), b'r') as err_log_file:
            stderr = err_log_file.read()

        return {
            u'workflow_ID': self.workflow_id,
            u'log': {
                u'cmd': [u''],
                u'startTime': u'',
                u'endTime': u'',
                u'stdout': u'',
                u'stderr': stderr,
                u'exitCode': exit_code
            }
        }

    def cancel(self):
        pass


def get_workflow_status(workflow_id):
    job = Workflow(workflow_id)
    return job.getstatus()


def get_workflow_log(workflow_id):
    job = Workflow(workflow_id)
    return job.getlog()


def cancel_workflow(workflow_id):
    job = Workflow(workflow_id)
    job.cancel()
    return job.getstatus()


def run_workflow(body):
    workflow_id = uuid.uuid4().hex
    job = Workflow(workflow_id)
    job.run(body[u'workflow_url'], body[u'input'])
    return job.getstatus()


def main():
    app = connexion.App(__name__, specification_dir=u'swagger/')

    def resolve(function_name):
        return utils.get_function_from_name(b'cwl_runner_wes.' + function_name)

    app.add_api(u'proto/workflow_execution.swagger.json', resolver=Resolver(resolve))

    app.run(port=8080)


if __name__ == u'__main__':
    main()

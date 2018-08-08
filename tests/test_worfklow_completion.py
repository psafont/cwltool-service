import pytest

import json

from workflow_service.models import State

from tests import app_client, request, wait_for_completion, workflows_and_inputs


def test_echo_workflow(app_client, workflows_and_inputs):
    _, client = app_client
    woflo, input_data = workflows_and_inputs[u'echo']
    status_code, data = request(client, u'post',
                                u'/run?wf=' + woflo,
                                data=input_data
                               )
    assert status_code == 200
    assert data[u'input'] == input_data
    assert u'id' in data

    job_id = data[u'id'].split('/')[-1]

    state = wait_for_completion(client, job_id, 30)

    _, log = request(client, u'get',
                     u'/jobs/' + job_id + u'/log'
                    )

def test_downloads(app_client, workflows_and_inputs):
    _, client = app_client
    woflo, input_data = workflows_and_inputs[u'createfile']
    status_code, data = request(client, u'post',
                                u'/run?wf=' + woflo,
                                data=input_data
                               )
    assert status_code == 200
    assert data[u'input'] == input_data
    assert u'id' in data

    job_id = data[u'id'].split('/')[-1]

    state = wait_for_completion(client, job_id, 30)

    _, log = request(client, u'get',
                     u'/jobs/' + job_id + u'/log'
                    )
    assert state == State.Complete.value, log

    status_code, data = request(client, u'get',
                                u'/jobs/' + job_id + u'/output/out',
                               )
    assert status_code == 200

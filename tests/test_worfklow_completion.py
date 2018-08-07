import pytest

from workflow_service.models import State

from tests import app_client, request, wait_for_completion, workflows_and_inputs


@pytest.mark.skip(reason="Udocker setup in CI is failing")
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

    state = wait_for_completion(client, job_id, 10)

    _, log = request(client, u'get',
                     u'/jobs/' + job_id + u'/log'
                    )
    assert state == State.Complete.value, log

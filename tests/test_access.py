import pytest

from tests import (
    app_client,
    request,
    token_authenticated,
    token_snooper,
    workflows_and_inputs
)

invalid_job_ids = [
    (u'None', u'None'),
    (u'Number', u'1'),
    (u'Random Letters', u'Im-a-job'),
    (u'Out of bounds UUID', u'00000000-0000-0000-0000-000000000000')
]
@pytest.mark.parametrize('name, jid', invalid_job_ids)
def test_invalid_jobids(name, jid, app_client):
    _, client = app_client
    for endpoint in ('', '/log', 'output/test'):
        status_code, _ = request(client, u'get',
                                 u'/jobs/' + jid + endpoint
                                )
        assert status_code == 404

def test_anonymous_user(app_client, workflows_and_inputs):
    woflo, input_data = workflows_and_inputs['echo']
    _, client = app_client

    status_code, data = request(client, u'post',
                                u'/run?wf=' + woflo,
                                data=input_data
                               )
    assert status_code == 200
    assert data[u'input'] == input_data
    assert u'id' in data

    job_id = data[u'id'].split('/')[-1]

    status_code, data = request(client, u'get',
                                u'/jobs/' + job_id
                               )
    assert status_code == 200

    status_code, data = request(client, u'get',
                                u'/jobs/' + job_id + u'/log'
                               )
    assert status_code == 200

    status_code, data = request(client, u'get', u'/jobs')
    assert status_code == 401
    assert data == {u'message': u'Request is missing the Authorization header'}

def test_token_user(app_client, workflows_and_inputs, token_authenticated):
    woflo, input_data = workflows_and_inputs['echo']
    _, client = app_client

    status_code, data = request(client, u'post',
                                u'/run?wf=' + woflo,
                                token=token_authenticated,
                                data=input_data
                               )
    assert status_code == 200
    assert data[u'input'] == input_data
    assert u'id' in data

    job_id = data[u'id'].split('/')[-1]

    status_code, data = request(client, u'get',
                                u'/jobs/' + job_id,
                                token=token_authenticated,
                               )
    assert status_code == 200

    status_code, data = request(client, u'get', u'/jobs', token=token_authenticated)
    assert status_code == 200

    id_list = [job[u'id'].split('/')[-1] for job in data]
    assert job_id in id_list,\
                  'The job id ({}) just created should be visible in /jobs'.format(job_id)

def test_anonymous_snooper(app_client, workflows_and_inputs, token_authenticated):
    woflo, input_data = workflows_and_inputs['echo']
    _, client = app_client

    status_code, data = request(client, u'post',
                                u'/run?wf=' + woflo,
                                token=token_authenticated,
                                data=input_data
                               )
    assert status_code == 200
    assert u'id' in data

    job_id = data[u'id'].split('/')[-1]

    status_code, data = request(client, u'get',
                                u'/jobs/' + job_id
                               )
    assert status_code == 404

def test_authenticated_snooper(
        app_client,
        workflows_and_inputs,
        token_authenticated,
        token_snooper
):
    woflo, input_data = workflows_and_inputs['echo']
    _, client = app_client

    status_code, data = request(client, u'post',
                                u'/run?wf=' + woflo,
                                token=token_authenticated,
                                data=input_data
                               )
    assert status_code == 200
    assert u'id' in data

    job_id = data[u'id'].split('/')[-1]

    status_code, data = request(client, u'get',
                                u'/jobs/' + job_id,
                                token=token_snooper
                               )
    assert status_code == 404

    status_code, data = request(client, u'get', u'/jobs', token=token_snooper)
    assert status_code == 200

    id_list = [job[u'id'].split('/')[-1] for job in data]
    assert job_id not in id_list,\
        'The job id ({}) from other users should not be visible in /jobs'.format(job_id)

def test_trailing_slashes(app_client, workflows_and_inputs):
    woflo, input_data = workflows_and_inputs['echo']
    _, client = app_client

    status_code, data = request(client, u'post',
                                u'/run?wf=' + woflo,
                                data=input_data
                               )
    assert status_code == 200
    assert data[u'input'] == input_data
    assert u'id' in data

    job_id = data[u'id'].split('/')[-1]

    status_code, data = request(client, u'get',
                                u'/jobs/' + job_id
                               )
    status_code_s, data_s = request(client, u'get',
                                    u'/jobs/' + job_id + '/'
                                   )
    assert status_code == status_code_s
    assert data == data_s

    status_code, data = request(client, u'get', u'/jobs')
    status_code_s, data_s = request(client, u'get', u'/jobs/')
    assert status_code == status_code_s
    assert data == data_s

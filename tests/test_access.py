import unittest2

from tests import configure_test_app, user_token, WOFLO, request


class TestEndPointAccess(unittest2.TestCase):
    def setUp(self):
        self.app, self.client = configure_test_app()
        self.token = user_token(self.app, u'jeff')
        self.token_other = user_token(self.app, u'nisu')
        self.woflo = WOFLO

    def test_invalid_jobids(self):
        not_really_jobs = [
            (u'None', u'None'),
            (u'Number', u'1'),
            (u'Random Letters', u'Im-a-job'),
            (u'Out of bounds UUID', u'00000000-0000-0000-0000-000000000000')
        ]
        for (name, not_a_good_job) in not_really_jobs:
            with self.subTest(token=name):
                status_code, _ = request(self.client, u'get',
                                         u'/jobs/' + not_a_good_job
                                        )
                self.assertEquals(status_code, 404)
                status_code, _ = request(self.client, u'get',
                                         u'/jobs/' + not_a_good_job + '/log'
                                        )
                self.assertEquals(status_code, 404)
                status_code, _ = request(self.client, u'get',
                                         u'/jobs/' + not_a_good_job + '/output/test'
                                        )
                self.assertEquals(status_code, 404)

    def test_anonymous_user(self):
        input_data = u'{"protein": "sp:wap_rat"}'
        status_code, data = request(self.client, u'post',
                                    u'/run?wf=' + self.woflo,
                                    data=input_data
                                   )
        self.assertEquals(status_code, 200)
        self.assertDictContainsSubset({u'input': input_data}, data)
        self.assertIn(u'id', data)

        job_id = data[u'id'].split('/')[-1]

        status_code, data = request(self.client, u'get',
                                    u'/jobs/' + job_id
                                   )
        self.assertEquals(status_code, 200)

        status_code, data = request(self.client, u'get', u'/jobs')
        self.assertEquals(status_code, 401)
        self.assertEquals(data, {u'message': u'Request is missing the Authorization header'})

    def test_token_user(self):
        input_data = u'{"protein": "sp:wap_rat"}'
        status_code, data = request(self.client, u'post',
                                    u'/run?wf=' + self.woflo,
                                    token=self.token,
                                    data=input_data
                                   )
        self.assertEquals(status_code, 200)
        self.assertDictContainsSubset({u'input': input_data}, data)
        self.assertIn(u'id', data)

        job_id = data[u'id'].split('/')[-1]

        status_code, data = request(self.client, u'get',
                                    u'/jobs/' + job_id,
                                    token=self.token,
                                   )
        self.assertEquals(status_code, 200)

        status_code, data = request(self.client, u'get', u'/jobs', token=self.token)
        self.assertEquals(status_code, 200)

        id_list = [job[u'id'].split('/')[-1] for job in data]
        self.assertIn(job_id, id_list,
                      'The job id ({}) just created should be visible in /jobs'.format(job_id))

    def test_anonymous_snooper(self):
        input_data = u'{"protein": "sp:wap_rat"}'
        status_code, data = request(self.client, u'post',
                                    u'/run?wf=' + self.woflo,
                                    token=self.token,
                                    data=input_data
                                   )
        self.assertEquals(status_code, 200)
        self.assertIn(u'id', data)

        job_id = data[u'id'].split('/')[-1]

        status_code, data = request(self.client, u'get',
                                    u'/jobs/' + job_id
                                   )
        self.assertEquals(status_code, 404)

    def test_authenticated_snooper(self):
        input_data = u'{"protein": "sp:wap_rat"}'
        status_code, data = request(self.client, u'post',
                                    u'/run?wf=' + self.woflo,
                                    token=self.token,
                                    data=input_data
                                   )
        self.assertEquals(status_code, 200)
        self.assertIn(u'id', data)

        job_id = data[u'id'].split('/')[-1]

        status_code, data = request(self.client, u'get',
                                    u'/jobs/' + job_id,
                                    token=self.token_other
                                   )
        self.assertEquals(status_code, 404)

        status_code, data = request(self.client, u'get', u'/jobs', token=self.token_other)
        self.assertEquals(status_code, 200)

        id_list = [job[u'id'].split('/')[-1] for job in data]
        self.assertNotIn(job_id, id_list,
                         'The job id ({}) from other users should not be visible in /jobs'
                         .format(job_id))

    def test_trailing_slashes(self):
        input_data = u'{"protein": "sp:wap_rat"}'
        status_code, data = request(self.client, u'post',
                                    u'/run?wf=' + self.woflo,
                                    data=input_data
                                   )
        self.assertEquals(status_code, 200)
        self.assertDictContainsSubset({u'input': input_data}, data)
        self.assertIn(u'id', data)

        job_id = data[u'id'].split('/')[-1]

        status_code, data = request(self.client, u'get',
                                    u'/jobs/' + job_id
                                   )
        status_code_s, data_s = request(self.client, u'get',
                                        u'/jobs/' + job_id + '/'
                                       )
        self.assertEquals(status_code, status_code_s)
        self.assertEquals(data, data_s)

        status_code, data = request(self.client, u'get', u'/jobs')
        status_code_s, data_s = request(self.client, u'get', u'/jobs/')
        self.assertEquals(status_code, status_code_s)
        self.assertEquals(data, data_s)


if __name__ == u'__main__':
    unittest2.main()

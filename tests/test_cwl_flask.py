# -*- coding: utf-8 -*-
"""
Test for CWL Flask
"""
from flask import json
from future.utils import viewitems
import unittest2
from flask_jwt_extended import JWTManager
from cwltoolservice import cwl_flask


class CwlFlaskTestCase(unittest2.TestCase):
    statuses = [
        {u'output': {u'some': u'thing'}},
        {u'output': {u'うんち': u'おどおど'}}
    ]

    def test_output_obj(self):
        for status in self.statuses:
            with self.subTest(status=status):
                for (key, value) in viewitems(status[u'output']):
                    self.assertEqual(cwl_flask.getoutputobj(status, key), value)

    def test_output_obj_fail(self):
        for status in self.statuses[:1]:
            with self.subTest(status=status):
                self.assertIsNone(cwl_flask.getoutputobj(status, u'non-existant'))


class TestEndPoints(unittest2.TestCase):
    def setUp(self):
        self.app = cwl_flask.APP
        self.app.private_key = u'???'
        self.app.config[u'JWT_IDENTITY_CLAIM'] = u'sub'
        self.jwt_manager = JWTManager(self.app)
        self.app.testing = True
        self.client = self.app.test_client()

    @staticmethod
    def _request(request, url, token=None, data=None):
        kwargs = dict()

        if token is not None:
            kwargs['header'] = {'Authorization': 'Bearer {}'.format(token)}
        if data is not None:
            kwargs['data'] = data

        response = request(url, follow_redirects=True, **kwargs)

        status_code = response.status_code
        data = json.loads(response.get_data(as_text=True))
        return status_code, data

    def test_anonymous_user(self):
        status_code, data = self._request(self.client.post,
                                          u'/run?wf=https://raw.githubusercontent.com/common-workflow-language/common-workflow-language/master/draft-3/examples/1st-tool.cwl',
                                          data=u'{"protein": "sp:wap_rat"}'
                                          )
        self.assertEquals(status_code, 200)
        self.assertDictContainsSubset({u'input': {u'protein': u'sp:wap_rat'}}, data)
        self.assertIn(u'id', data)

        job_id = data[u'id'].split('/')[-1]

        status_code, data = self._request(self.client.get,
                                          u'/jobs/' + job_id
                                          )
        self.assertEquals(status_code, 200)

        status_code, data = self._request(self.client.get, u'/jobs')
        self.assertEquals(status_code, 401)
        self.assertEquals(data, {u'msg': u'Missing Authorization Header'})


if __name__ == u'__main__':
    unittest2.main()

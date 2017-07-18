# -*- coding: utf-8 -*-
"""
Test for CWL Flask
"""
from future.utils import viewitems

import unittest2

from flask import json

from cryptography import x509
from cryptography.hazmat.backends import default_backend
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
        self.app.testing = True

        self.wf = u'https://raw.githubusercontent.com/common-workflow-language/common-workflow-language/master/draft-3/examples/1st-tool.cwl'

        self.app.config[u'JWT_IDENTITY_CLAIM'] = u'sub'
        self.app.config[u'JWT_PRIVATE_KEY'] = u'''
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAl897jsaYfcQY3p2GqXJkMNGvgXQisasv+iIuE+ibVRK5B2TD
ZVt2xJ1iXnvuXVlfIgXo4MFo8N4QRp0sa4nG+q+NVy+pynNH1fcHdm9uuGeZhwYe
lJTfM7ALVYPKYzxpfeDzaq3Iy20W9wVqhxNvtoXa17fPq1OQqLR2GmgZQRgNiCN1
iKQ4qLBc1E2bzW0N1H8qMA+r0U5ph2FSlfzSH+D9gvzbvOeScdO4xMywngb2Jp33
+gK4Q1EUGx2RMrAB+3P/CdNpnEk4QC9gPlfAVOu15vzFqgf8+TgWQjJvKt08/XKD
6Q5K14mprCko4rV7bcT3t/OL8OdM+cYt0NmWxwIDAQABAoIBAF1SN3MyVAVj6aHX
ljNN1ZdJHylmGfm78TdDka29XNd0Nff8kj0Zd64vzYulhYcu7FM+7MRVQMxoxfqS
nf7RaFcsWaeR7j88lJlMTPMaVybW0ML3GQ9fYMImYyFDbcOJHJQ8F4apo/iha++Y
Db9RTGgYasoW/XslWJTMsplTCss/KjNR49H+JW3pO+Lc7OLwSwQRhK5YgslT9EXU
zQIhVdXV3GdUzsVN/AGfu9y5i4nMRXgIEshFNLKGJ/2u27LdPjw2abEifEg1DVud
qdRcvRv+d8chcZjoCeGpbW/eo5ORVazo0NzMt5z2MLrz3o4hVhSm/wrcASenGYPf
VW7uOKECgYEA0NjoaEDdVSpL0ShkAMCHRMr23l0+PXFyLCHWiQBx9+S6O5Ujy1Kz
3PkTI8rZMJbZduFyPILhU8Hpm8UZpRifinhkPQe+9nfZyZ7IYqrnjtosRume/Og6
iyzNtVt0yjAiQkVRczvOAaL7ANGXMEXQjyNadrzgDr3Ay8ztkylUqRECgYEAuhXs
da18WulnMljWEUTFUIerm/W1e88GpTQfmjGD9unsyOYOWf3nxzC1KPRzt7jkg9zN
d0FFQ3BZkdf2wobVRMAD6FC7zZsJxVAkWvqsuOzlClak9I5FRVuQzzFhEhOw6ZYS
oR8JKksL+G97XyQnoveeHCMiTrTwA7Ukiy+iAlcCgYEAp0u6EBk1s40oIqnqQbf4
I6E6VDH5M5r2zGdmxWQ3502v6R61B6B+OBrFvDw38vZDyTkbG2H0QfXpvkALJPcu
heue0EyuKh0jtqCdAHzK9OHL6homo40bqHUBa6+RRI1+Q/vnHRnhEeqOir9aDu89
/Atj4g22pdhW4mqMPQA0syECgYB/SB2sRFUJ7ho7Ms6Bk1OPiK0WCVPwcqPt/iAb
nQDRtCHVLJ7maSjPc36Gm+ZG5X3QwAf+KTQSM9fgTSMo3Yck9l312rsKoKBnSTEE
1e+sscTcdHVyHZo+HaqIPhNShQt+SrtFX/Ap8JkofkCZzCYcb1jDkDiYM2T0dEOh
vJwJEwKBgQCgnWy5ek2Uw2m1yitmHJ3wSIykbTr44I3W2SbnAhS2JtaKa9HSMfBZ
q3SN3qyDqHPrF4tGMpU9yXBx6EKKHKx3tzSv99BWOGlAaU7hHHFRUvJDE+DhKOSY
ThIJrr1FbD1Wo69AVrMDSRz7+8PYf1FHoLPktf9Fsbkeha0uO7mPkw==
-----END RSA PRIVATE KEY-----'''
        pem_data = u'''
-----BEGIN CERTIFICATE-----
MIIDezCCAmOgAwIBAgIEasdlvzANBgkqhkiG9w0BAQsFADBuMQswCQYDVQQGEwJV
SzEXMBUGA1UECBMOQ2FtYnJpZGdlc2hpcmUxEDAOBgNVBAcTB0hpbnh0b24xDDAK
BgNVBAoTA0VCSTEMMAoGA1UECxMDVFNJMRgwFgYDVQQDEw9QYXUgUnVpeiBTYWZv
bnQwHhcNMTYwODIyMDkwNDA1WhcNMTYxMTIwMDkwNDA1WjBuMQswCQYDVQQGEwJV
SzEXMBUGA1UECBMOQ2FtYnJpZGdlc2hpcmUxEDAOBgNVBAcTB0hpbnh0b24xDDAK
BgNVBAoTA0VCSTEMMAoGA1UECxMDVFNJMRgwFgYDVQQDEw9QYXUgUnVpeiBTYWZv
bnQwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQCXz3uOxph9xBjenYap
cmQw0a+BdCKxqy/6Ii4T6JtVErkHZMNlW3bEnWJee+5dWV8iBejgwWjw3hBGnSxr
icb6r41XL6nKc0fV9wd2b264Z5mHBh6UlN8zsAtVg8pjPGl94PNqrcjLbRb3BWqH
E2+2hdrXt8+rU5CotHYaaBlBGA2II3WIpDiosFzUTZvNbQ3UfyowD6vRTmmHYVKV
/NIf4P2C/Nu855Jx07jEzLCeBvYmnff6ArhDURQbHZEysAH7c/8J02mcSThAL2A+
V8BU67Xm/MWqB/z5OBZCMm8q3Tz9coPpDkrXiamsKSjitXttxPe384vw50z5xi3Q
2ZbHAgMBAAGjITAfMB0GA1UdDgQWBBQ/ehcr+Gb+wEsAi59ARhKiRq+XMzANBgkq
hkiG9w0BAQsFAAOCAQEAP702ZqTyE6FYlbhQG+39XYpYkKGI+yPCEHYNRDzSUqBF
YH5FNs54yzBwXTQzqPLMHCYN9ahR7X16A5uLr9dDiJ01DQIPrt1utRL9XvMTHnO6
R/Joq1Mf4T1QuVEFwdy0SVh3ekXHH4BXcXB+epSwobssThKNnoeHYYa1tu8rMveM
EBo+qvEFdfZ1SumH3g+3oQYlyHxWdYHjd2QFkF6460YzfkdV1zsuGEDrctlOEQZU
7wTt4Or1gJoVZEtW/qdnslll71UnCIGn0TnLuC/cy/1dbMpq/1hM+JGk+aNQE4Qh
NOqbOxbFp+hObyESwGdHbRlBCfGS+thrW5Q1lROMgg==
-----END CERTIFICATE-----
'''.encode()

        cert = x509.load_pem_x509_certificate(pem_data, default_backend())
        self.app.config[u'JWT_PUBLIC_KEY'] = cert.public_key()

        self.app.config[u'JWT_ALGORITHM'] = u'RS256'
        self.jwt_manager = JWTManager(self.app)

        self.client = self.app.test_client()

        with self.app.test_request_context():
            self.token = self.jwt_manager.create_access_token(identity=u'jeff')
            self.token_other = self.jwt_manager.create_access_token(identity=u'nisu')

    @staticmethod
    def _request(client, verb, url, token=None, data=None):
        kwargs = dict()

        if verb == u'post':
            request = client.post
        else:
            request = client.get

        if token is not None:
            kwargs[u'headers'] = {u'Authorization': u'Bearer {}'.format(token)}
        if data is not None:
            kwargs[u'data'] = data

        response = request(url, **kwargs)

        if response.status_code == 303:
            kwargs.pop(u'data')
            response = client.get(response.headers[u'Location'], **kwargs)

        status_code = response.status_code
        data = json.loads(response.get_data(as_text=True))
        return status_code, data

    def test_anonymous_user(self):
        status_code, data = self._request(self.client, u'post',
                                          u'/run?wf=' + self.wf,
                                          data=u'{"protein": "sp:wap_rat"}'
                                          )
        self.assertEquals(status_code, 200)
        self.assertDictContainsSubset({u'input': {u'protein': u'sp:wap_rat'}}, data)
        self.assertIn(u'id', data)

        job_id = data[u'id'].split('/')[-1]

        status_code, data = self._request(self.client, u'get',
                                          u'/jobs/' + job_id
                                          )
        self.assertEquals(status_code, 200)

        status_code, data = self._request(self.client, u'get', u'/jobs')
        self.assertEquals(status_code, 401)
        self.assertEquals(data, {u'msg': u'Missing Authorization Header'})

    def test_token_user(self):

        status_code, data = self._request(self.client, u'post',
                                          u'/run?wf=' + self.wf,
                                          token=self.token,
                                          data=u'{"protein": "sp:wap_rat"}'
                                          )
        self.assertEquals(status_code, 200)
        self.assertDictContainsSubset({u'input': {u'protein': u'sp:wap_rat'}}, data)
        self.assertIn(u'id', data)

        job_id = data[u'id'].split('/')[-1]

        status_code, data = self._request(self.client, u'get',
                                          u'/jobs/' + job_id,
                                          token=self.token,
                                          )
        self.assertEquals(status_code, 200)

        status_code, data = self._request(self.client, u'get', u'/jobs', token=self.token)
        id_list = [job[u'id'].split('/')[-1] for job in data]
        self.assertEquals(status_code, 200)
        self.assertIn(job_id, id_list,
                      'The job id ({}) just created should be visible in /jobs'.format(job_id))

    def test_anonymous_snooper(self):

        status_code, data = self._request(self.client, u'post',
                                          u'/run?wf=' + self.wf,
                                          token=self.token,
                                          data=u'{"protein": "sp:wap_rat"}'
                                          )
        self.assertEquals(status_code, 200)
        self.assertIn(u'id', data)

        job_id = data[u'id'].split('/')[-1]

        status_code, data = self._request(self.client, u'get',
                                          u'/jobs/' + job_id
                                          )
        self.assertEquals(status_code, 404)

    def test_authenticated_snooper(self):

        status_code, data = self._request(self.client, u'post',
                                          u'/run?wf=' + self.wf,
                                          token=self.token,
                                          data=u'{"protein": "sp:wap_rat"}'
                                          )
        self.assertEquals(status_code, 200)
        self.assertIn(u'id', data)

        job_id = data[u'id'].split('/')[-1]

        status_code, data = self._request(self.client, u'get',
                                          u'/jobs/' + job_id,
                                          token=self.token_other
                                          )
        self.assertEquals(status_code, 404)


if __name__ == u'__main__':
    unittest2.main()

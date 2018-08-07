import time
from calendar import timegm
from datetime import datetime

import pytest

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from flask import json

from aap_client.tokens import encode_token
from aap_client.flask.client import JWTClient
from workflow_service import server
from workflow_service.models import State

# pylint: disable=line-too-long
@pytest.fixture
def workflows_and_inputs():
    return {
        u'echo': (
            u'https://raw.githubusercontent.com/common-workflow-language/common-workflow-language/master/v1.0/examples/1st-tool.cwl',
            u'{"message": "sp:wap_rat"}'
        ),
        u'createfile': (
            u'https://raw.githubusercontent.com/common-workflow-language/common-workflow-language/master/v1.0/examples/createfile.cwl'
            u'file content'
        )
    }

PEM_DATA = u'''
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
X509_DATA = u'''
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

CERT = x509.load_pem_x509_certificate(X509_DATA, default_backend())


@pytest.fixture
def app_client():
    app = server.APP
    app.testing = True

    app.config[u'JWT_PUBLIC_KEY'] = CERT.public_key()
    app.config[u'JWT_ALGORITHM'] = u'RS256'

    JWTClient(app)

    client = app.test_client()

    return app, client


def user_token(app, user):
    default_claims = {
        u'iat': now(),
        u'exp': now() + 3600,
        u'iss': u'aap.ebi.ac.uk',
        u'sub': u'usr-a1d0c6e83f027327d8461063f4ac58a6',
        u'email': u'subject@ebi.ac.uk',
        u'name': u'John Doe',
        u'nickname': u'73475cb40a568e8da8a045ced110137e159f890ac4da883b6b17dc651b3a8049'
    }

    claims = default_claims.copy()
    claims[u'sub'] = user

    with app.test_request_context():
        token = encode_token(claims, PEM_DATA)

    return token


@pytest.fixture
def token_authenticated(app_client):
    return user_token(app_client[0], u'jeff')


@pytest.fixture
def token_snooper(app_client):
    return user_token(app_client[0], u'nisu')


def now():
    return timegm(datetime.utcnow().utctimetuple())


def request(client, verb, url, token=None, data=None):
    kwargs = dict()

    if verb == u'post':
        req = client.post
    else:
        req = client.get

    if token is not None:
        kwargs[u'headers'] = {u'Authorization': u'Bearer {}'.format(token)}
    if data is not None:
        kwargs[u'data'] = data

    response = req(url, **kwargs)

    if response.status_code == 303:
        kwargs.pop(u'data')
        response = client.get(response.headers[u'Location'], **kwargs)

    status_code = response.status_code
    try:
        data = json.loads(response.get_data(as_text=True))
    except ValueError:
        pass
        # pass data as-is, without deserializing (for logs)
    return status_code, data

def wait_for_completion(client, job_id, timeout):
    running = True
    overdue = False
    start = time.time()
    while running and not overdue:
        status_code, data = request(client, u'get',
                                    u'/jobs/' + job_id
                                   )
        assert status_code == 200
        if u'state' in data and data[u'state'] != State.Running.value:
            running = False
        overdue = time.time() - start > timeout
    return data[u'state']

import time
import unittest2

from workflow_service.models import State
from tests import configure_test_app, WOFLOS, request


class TestEndPointAccess(unittest2.TestCase):
    def setUp(self):
        self.app, self.client = configure_test_app()
        self.woflos = WOFLOS

    @unittest2.skip('Fails on CI because of (u)docker setup')
    def test_echo_workflow(self):
        woflo, input_data = self.woflos[u'echo']
        status_code, data = request(self.client, u'post',
                                    u'/run?wf=' + woflo,
                                    data=input_data
                                   )
        self.assertEquals(status_code, 200)
        self.assertDictContainsSubset({u'input': input_data}, data)
        self.assertIn(u'id', data)

        job_id = data[u'id'].split('/')[-1]

        running = True
        overdue = False
        start = time.time()
        while running and not overdue:
            status_code, data = request(self.client, u'get',
                                        u'/jobs/' + job_id
                                       )
            self.assertEquals(status_code, 200)
            if u'state' in data and data[u'state'] != State.Running.value:
                running = False
            overdue = time.time() - start > 10

        _, log = request(self.client, u'get',
                         u'/jobs/' + job_id + u'/log'
                        )
        self.assertEquals(data[u'state'], State.Complete.value, log)
if __name__ == u'__main__':
    unittest2.main()

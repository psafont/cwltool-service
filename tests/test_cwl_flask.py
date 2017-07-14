# -*- coding: utf-8 -*-
"""
Test for CWL Flask
"""
from future.utils import viewitems
import unittest2
import cwltoolservice.cwl_flask


class CwlFlaskTestCase(unittest2.TestCase):
    statuses = [
        {u'output': {u'some': u'thing'}},
        {u'output': {u'うんち': u'おどおど'}}
    ]

    def test_output_obj(self):
        for status in self.statuses:
            with self.subTest(status=status):
                for (key, value) in viewitems(status[u'output']):
                    self.assertEqual(cwltoolservice.cwl_flask.getoutputobj(status, key), value)

    def test_output_obj_fail(self):
        for status in self.statuses[:1]:
            with self.subTest(status=status):
                self.assertIsNone(cwltoolservice.cwl_flask.getoutputobj(status, u'non-existant'))


if __name__ == u'__main__':
    unittest2.main()

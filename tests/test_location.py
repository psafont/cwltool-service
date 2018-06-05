#pylint: disable=line-too-long
"""
Tests for output and location handling
"""
from future.utils import viewitems

import unittest2

from workflow_service import server


class OutputLocationTestCase(unittest2.TestCase):

    def test_retrieve_outputs(self):
        for status in self.statuses.values():
            with self.subTest(status=status):
                for (key, value) in viewitems(status[u'output']):
                    self.assertEqual(server.getoutputobj(status, key), value)

    def test_retrieve_invented_output(self):
        for status in self.statuses.values():
            with self.subTest(status=status):
                self.assertIsNone(server.getoutputobj(status, u'non-existant'))

    def test_output_location(self):
        for status in self.statuses.values():
            with self.subTest(status=status):
                server.change_all_locations(status[u'output'], u'http://server/jobs/42')

    def test_retrieve_outputs_in_list(self):
        for outputid in [u'all-out/0', u'all-out/1', u'all-out/2', u'xml']:
            self.assertNotEqual(server.getoutputobj(self.statuses[u'in-list'], outputid), None)

        for outputid in [u'all-out/3', u'all-out//', u'foo/bar', u'']:
            self.assertIsNone(server.getoutputobj(self.statuses[u'in-list'], outputid))

    statuses = {
        u"in-list": {u"output": {
            u"all-out": [
                {
                    u"basename": u"ncbiblast-R20180115-115228-0052-96975235-pg.complete-visual-jpg.jpg",
                    u"checksum": u"sha1$5bf98ff2f80efeefd69d8dc68e8d7f286d4baa62",
                    u"class": u"File",
                    u"location": u"file:///tmp/tmpyBLhuL/ncbiblast-R20180115-115228-0052-96975235-pg.complete-visual-jpg.jpg",
                    u"path": u"/tmp/tmpyBLhuL/ncbiblast-R20180115-115228-0052-96975235-pg.complete-visual-jpg.jpg",
                    u"size": 1272193
                },
                {
                    u"basename": u"ncbiblast-R20180115-115228-0052-96975235-pg.complete-visual-png.png",
                    u"checksum": u"sha1$25a346fa20ae8f8904af4ff701e33f5fbfd481e6",
                    u"class": u"File",
                    u"location": u"file:///tmp/tmpyBLhuL/ncbiblast-R20180115-115228-0052-96975235-pg.complete-visual-png.png",
                    u"path": u"/tmp/tmpyBLhuL/ncbiblast-R20180115-115228-0052-96975235-pg.complete-visual-png.png",
                    u"size": 1124966
                },
                {
                    u"basename": u"ncbiblast-R20180115-115228-0052-96975235-pg.ids.txt",
                    u"checksum": u"sha1$4496b05e10dab7227c9d83bc29820831909515b5",
                    u"class": u"File",
                    u"location": u"file:///tmp/tmpyBLhuL/ncbiblast-R20180115-115228-0052-96975235-pg.ids.txt",
                    u"path": u"/tmp/tmpyBLhuL/ncbiblast-R20180115-115228-0052-96975235-pg.ids.txt",
                    u"size": 8318
                },
            ],
            u"xml": {
                u"basename": u"ncbiblast-R20180115-115228-0052-96975235-pg.xml.xml",
                u"checksum": u"sha1$c696fc13d0f64706245a0a136773463eebc091fa",
                u"class": u"File",
                u"location": u"/tmp/tmpyBLhuL/ncbiblast-R20180115-115228-0052-96975235-pg.xml.xml",
                u"path": u"/tmp/tmpyBLhuL/ncbiblast-R20180115-115228-0052-96975235-pg.xml.xml",
                u"size": 443635
            }
        }},
        u"empty": {u"output": {
        }}
    }

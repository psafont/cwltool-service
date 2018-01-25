# -*- coding: utf-8 -*-
#pylint: disable=line-too-long
"""
Tests for location handling
"""
from future.utils import viewitems

import unittest2

from wes_server import server


class CwlFlaskTestCase(unittest2.TestCase):

    def test_output_obj(self):
        for status in self.statuses:
            with self.subTest(status=status):
                for (key, value) in viewitems(status[u'output']):
                    self.assertEqual(server.getoutputobj(status, key), value)

    def test_output_obj_fail(self):
        for status in self.statuses[:1]:
            with self.subTest(status=status):
                self.assertIsNone(server.getoutputobj(status, u'non-existant'))

    def test_output_location(self):
        for status in self.statuses:
            with self.subTest(status=status):
                server.change_all_locations(status[u'output'], u'http://server/jobs/42')

    def test_get_output(self):
        for outputid in [u'all-out/0', u'all-out/1', u'all-out/2', u'xml']:
            self.assertNotEqual(server.getoutputobj(self.statuses[0], outputid), None)

        for outputid in [u'all-out/3', u'all-out//', u'foo/bar', u'']:
            self.assertIsNone(server.getoutputobj(self.statuses[0], outputid))

    statuses = [
        {
            u"id": u"http://server/jobs/42",
            u"input": {
                u"database": "uniprotkb",
                u"email": u"ebi_glue@ebi.ac.uk",
                u"program": u"blastp",
                u"sequence": u"MALWTRLLPLLALLALWAPAPAQAFVNQHLCGSHLVEALYLVCGERGFFYTPKARREAENJ\nPQAGAVELGGGLGGLQALALEGPPQKRGIVEQCCTSICSLYQLENYCN",
                u"stype": u"protein"
            },
            u"log": u"http://server/jobs/42/log",
            u"output": {
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
            },
            u"run": u"https://raw.githubusercontent.com/esanzgar/webservice-cwl/webprod/docker_cwls/ncbiblast.cwl",
            u"state": u"Complete"
        }
    ]

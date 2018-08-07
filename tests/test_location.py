#pylint: disable=line-too-long
"""
Tests for output and location handling
"""
from future.utils import viewitems

import pytest

from workflow_service import server

status_with_name = {
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
statuses = [value for key, value in viewitems(status_with_name)]

@pytest.mark.parametrize('status', statuses)
def test_retrieve_outputs(status):
    for (key, value) in viewitems(status[u'output']):
        assert server.getoutputobj(status, key) == value

@pytest.mark.parametrize('status', statuses)
def test_retrieve_invented_output(status):
    assert server.getoutputobj(status, u'non-existant') is None

@pytest.mark.parametrize('status', statuses)
def test_output_location(status):
    server.change_all_locations(status[u'output'], u'http://server/jobs/42')

def test_retrieve_outputs_in_list():
    in_list = status_with_name['in-list']
    for outputid in [u'all-out/0', u'all-out/1', u'all-out/2', u'xml']:
        assert server.getoutputobj(in_list, outputid) is not None

    for outputid in [u'all-out/3', u'all-out//', u'foo/bar', u'']:
        assert server.getoutputobj(in_list, outputid) is None

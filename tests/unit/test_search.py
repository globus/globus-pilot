import os
from pilot.search import update_metadata, scrape_metadata
from tests.unit.mocks import ANALYSIS_FILE_BASE_DIR
from pilot import client

MIXED_FILE = os.path.join(ANALYSIS_FILE_BASE_DIR, 'mixed.tsv')
NUMBERS_FILE = os.path.join(ANALYSIS_FILE_BASE_DIR, 'numbers.tsv')


def test_scrape_metadata(mock_config, mock_projects):
    pc = client.PilotClient()
    pc.project.current_project = 'foo-project'
    pc.profile.name = 'Marie Curie'
    meta = scrape_metadata(MIXED_FILE, 'https://foo.com', pc)
    dc_content = ['titles', 'creators', 'subjects', 'publicationYear',
                  'publisher', 'resourceType', 'dates', 'formats', 'version']

    assert all([c in meta['dc'].keys() for c in dc_content])
    assert meta['dc']['formats'] == ['text/tab-separated-values']
    assert meta['dc']['version'] == '1'
    assert meta['dc']['creators'][0]['creatorName'] == 'Curie, Marie'
    assert set(meta.keys()) == {'dc', 'files', 'ncipilot', 'field_metadata'}


def test_update_metadata_new_record_w_meta(mock_config):
    pc = client.PilotClient()
    pc.project.current_project = 'foo-project'
    pc.profile.name = 'Marie Curie'
    rec = scrape_metadata(MIXED_FILE, 'https://foo.com', pc)

    meta = update_metadata(rec, None, {'mime_type': 'csv'})
    assert meta['dc']['formats'] == ['csv']


def test_update_metadata_new_file(mock_config):
    pc = client.PilotClient()
    pc.project.current_project = 'foo-project'
    pc.profile.name = 'Marie Curie'
    old = scrape_metadata(MIXED_FILE, 'globus://foo.com', pc)
    new = scrape_metadata(NUMBERS_FILE, 'globus://bar.com', pc)

    meta = update_metadata(new, old, {})
    assert meta['files'] == new['files']


def test_update_metadata_prev_record(mock_config):
    pc = client.PilotClient()
    pc.project.current_project = 'foo-project'
    pc.profile.name = 'Marie Curie'
    old = scrape_metadata(MIXED_FILE, 'globus://foo.com', pc)
    pc.profile.name = 'Marie S Curie'
    new = scrape_metadata(MIXED_FILE, 'globus://foo.com', pc)

    assert new != old
    assert old['dc']['creators'][0]['creatorName'] == 'Curie, Marie'

    meta = update_metadata(new, old, {})
    assert meta['dc']['creators'][0]['creatorName'] == 'Curie, Marie S'
    assert meta['files'] == new['files'] == old['files']

import os
from pilot.search import update_metadata, scrape_metadata
from tests.unit.mocks import ANALYSIS_FILE_BASE_DIR

MIXED_FILE = os.path.join(ANALYSIS_FILE_BASE_DIR, 'mixed.tsv')
NUMBERS_FILE = os.path.join(ANALYSIS_FILE_BASE_DIR, 'numbers.tsv')


def test_scrape_metadata(mock_cli, mock_profile):
    meta = scrape_metadata(MIXED_FILE, 'https://foo.com', mock_cli)
    dc_content = ['titles', 'creators', 'subjects', 'publicationYear',
                  'publisher', 'resourceType', 'dates', 'formats', 'version']

    assert all([c in meta['dc'].keys() for c in dc_content])
    assert meta['dc']['formats'] == ['text/tab-separated-values']
    assert meta['dc']['version'] == '1'
    assert meta['dc']['creators'][0]['creatorName'] == 'Franklin, Rosalind'
    assert set(meta.keys()) == {'dc', 'files', 'project_metadata'}
    assert 'field_metadata' in meta['files'][0].keys()
    assert 'foo-project' == meta['project_metadata']['project-slug']


def test_update_metadata_new_record_w_meta(mock_cli):
    rec = scrape_metadata(MIXED_FILE, 'https://foo.com', mock_cli)
    meta = update_metadata(rec, None, {'mime_type': 'csv'})
    assert meta['dc']['formats'] == ['csv']


def test_update_metadata_new_file(mock_cli):
    old = scrape_metadata(MIXED_FILE, 'globus://foo.com', mock_cli)
    new = scrape_metadata(NUMBERS_FILE, 'globus://bar.com', mock_cli)

    meta = update_metadata(new, old, {})
    assert meta['files'] == new['files']


def test_update_metadata_prev_record(mock_cli, mock_profile):
    old = scrape_metadata(MIXED_FILE, 'globus://foo.com', mock_cli)
    mock_cli.profile.name = 'Marie Curie'
    new = scrape_metadata(MIXED_FILE, 'globus://foo.com', mock_cli)

    assert new != old
    assert old['dc']['creators'][0]['creatorName'] == 'Franklin, Rosalind'

    meta = update_metadata(new, old, {})
    assert meta['dc']['creators'][0]['creatorName'] == 'Curie, Marie'
    assert meta['files'] == new['files'] == old['files']

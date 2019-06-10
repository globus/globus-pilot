import os
from pilot.search import update_metadata, scrape_metadata
from tests.unit.mocks import ANALYSIS_FILE_BASE_DIR

MIXED_FILE = os.path.join(ANALYSIS_FILE_BASE_DIR, 'mixed.tsv')
NUMBERS_FILE = os.path.join(ANALYSIS_FILE_BASE_DIR, 'numbers.tsv')


def test_scrape_metadata(mock_config):
    mock_config.data['profile'] = {'name': 'Marie Skłodowska Curie'}
    meta = scrape_metadata(MIXED_FILE, 'https://foo.com')
    dc_content = ['titles', 'creators', 'subjects', 'publicationYear',
                  'publisher', 'resourceType', 'dates', 'formats', 'version']

    assert all([c in meta['dc'].keys() for c in dc_content])
    assert meta['dc']['formats'] == ['text/tab-separated-values']
    assert meta['dc']['version'] == '1'
    assert meta['dc']['creators'][0]['creatorName'] == ('Curie, '
                                                        'Marie Skłodowska')
    assert set(meta.keys()) == {'dc', 'files', 'ncipilot', 'field_metadata'}


def test_update_metadata_new_record_w_meta(mock_config):
    mock_config.data['profile'] = {'name': 'Marie Curie'}
    rec = scrape_metadata(MIXED_FILE, 'https://foo.com')

    meta = update_metadata(rec, None, {'mime_type': 'csv',
                                       })
    assert meta['dc']['formats'] == ['csv']


def test_update_metadata_new_file(mock_config):
    mock_config.data['profile'] = {'name': 'Marie Curie'}
    old = scrape_metadata(MIXED_FILE, 'globus://foo.com')
    new = scrape_metadata(NUMBERS_FILE, 'globus://bar.com')

    meta = update_metadata(new, old, {})
    assert meta['files'] == new['files']


def test_update_metadata_prev_record(mock_config):
    mock_config.data['profile'] = {'name': 'Marie Curie'}
    old = scrape_metadata(MIXED_FILE, 'globus://foo.com')
    mock_config.data['profile'] = {'name': 'Marie Skłodowska Curie'}
    new = scrape_metadata(MIXED_FILE, 'globus://foo.com')

    assert new != old
    assert old['dc']['creators'][0]['creatorName'] == 'Curie, Marie'

    meta = update_metadata(new, old, {})
    assert meta['dc']['creators'][0]['creatorName'] == ('Curie, '
                                                        'Marie Skłodowska')
    assert meta['files'] == new['files'] == old['files']

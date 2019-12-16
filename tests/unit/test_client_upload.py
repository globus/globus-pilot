import os
import pytest
import json
from unittest.mock import Mock

import globus_sdk
import jsonschema
from pilot.search import scrape_metadata
from pilot import exc, analysis
from pilot.exc import AnalysisException
from tests.unit.mocks import COMMANDS_FILE_BASE_DIR, MULTI_FILE_DIR

EMPTY_TEST_FILE = os.path.join(COMMANDS_FILE_BASE_DIR,
                               'test_file_zero_length.txt')
EMTPY_TEST_FILE_META = os.path.join(COMMANDS_FILE_BASE_DIR,
                                    'empty_file_metadata.json')
SMALL_TEST_FILE = os.path.join(COMMANDS_FILE_BASE_DIR, 'test_file_small.txt')
CUSTOM_METADATA = os.path.join(COMMANDS_FILE_BASE_DIR, 'custom_metadata.json')
INVALID_METADATA = os.path.join(COMMANDS_FILE_BASE_DIR,
                                'invalid_metadata.json')


def test_file_upload(mock_cli, mock_transfer_log, mock_search_client):
    # Should not raise errors
    metadata = mock_cli.upload(EMPTY_TEST_FILE, 'my_folder')
    assert set(metadata['new_metadata']) == {'files', 'dc', 'project_metadata'}
    assert metadata['files_modified'] is True
    assert metadata['metadata_modified'] is True
    assert metadata['protocol'] == 'globus'
    from pprint import pprint
    pprint(metadata)
    assert mock_search_client.ingest.called
    # This is a nice way to ensure the transfer was initiated
    assert mock_transfer_log.called


def test_dir_upload(mock_cli, mock_transfer_log):
    # Should not raise errors
    metadata = mock_cli.upload(MULTI_FILE_DIR, 'my_folder')['new_metadata']
    assert set(metadata) == {'files', 'dc', 'project_metadata'}
    assert len(metadata['files']) == 4
    expected_paths = [
        'my_folder/multi_file/text_metadata.txt',
        'my_folder/multi_file/folder/tsv1.tsv',
        'my_folder/multi_file/folder/tinyimage.png',
        'my_folder/multi_file/folder/folder2/tsv2.tsv',
    ]
    expected_urls = [mock_cli.get_globus_http_url(u) for u in expected_paths]
    urls = [f['url'] for f in metadata['files']]
    for url in urls:
        assert url in expected_urls


def test_update_mfe_with_file(mock_cli, mock_transfer_log,
                              mock_multi_file_result):
    sub = mock_cli.get_subject_url('my_folder/multi_file')
    mock_multi_file_result['gmeta'][0]['subject'] = sub
    gse = Mock(return_value=mock_multi_file_result['gmeta'])
    mock_cli.list_entries = gse
    metadata = mock_cli.upload(EMPTY_TEST_FILE, 'my_folder/multi_file',
                               update=True)['new_metadata']
    assert len(mock_multi_file_result['gmeta'][0]['content'][0]['files']) == 4
    assert len(metadata['files']) == 5
    urls = [f['url'] for f in metadata['files']]
    new_url = mock_cli.get_globus_http_url('my_folder/multi_file/' +
                                           os.path.basename(EMPTY_TEST_FILE))
    assert new_url in urls


def test_update_mfe_with_dir(mock_cli, mock_transfer_log,
                             mock_multi_file_result):
    sub = mock_cli.get_subject_url('my_folder/multi_file')
    mock_multi_file_result['gmeta'][0]['subject'] = sub
    gse = Mock(return_value=mock_multi_file_result['gmeta'])
    mock_cli.list_entries = gse
    metadata = mock_cli.upload(MULTI_FILE_DIR, 'my_folder/multi_file',
                               update=True)['new_metadata']
    assert len(mock_multi_file_result['gmeta'][0]['content'][0]['files']) == 4
    assert len(metadata['files']) == 8


def test_upload_in_dir_with_similar_record(mock_cli, mock_search_result):
    """
    This was to fix a bug where uploading similar records would cause conflicts

    * my_folder/simple_tsv
    * my_folder/empty_test_file.txt
    """
    sub = mock_cli.get_subject_url('my_folder/simple_tsv')
    mock_search_result['subject'] = sub
    gse = Mock(return_value=[mock_search_result])
    mock_cli.list_entries = gse
    # should not raise RecordExists Exception
    mock_cli.upload(EMPTY_TEST_FILE, 'my_folder')


def test_upload_without_destination(mock_cli):
    with pytest.raises(exc.NoDestinationProvided):
        mock_cli.upload(EMPTY_TEST_FILE, None)


def test_upload_to_nonexistant_dir(mock_cli, mock_transfer_error):
    mock_transfer_error.code = 'ClientError.NotFound'
    mock_cli.ls = Mock(side_effect=globus_sdk.exc.TransferAPIError)
    with pytest.raises(exc.DirectoryDoesNotExist):
        mock_cli.upload(EMPTY_TEST_FILE, 'my_folder')


def test_upload_destination_is_record(mock_cli, mock_multi_file_result):
    mock_cli.search.return_value = mock_multi_file_result
    with pytest.raises(exc.RecordExists):
        mock_cli.upload(EMPTY_TEST_FILE, '/multi_file/foo')


def test_upload_unexpected_ls_error(mock_cli, mock_transfer_error):
    mock_transfer_error.code = 'UnexpectedError'
    mock_cli.ls = Mock(side_effect=globus_sdk.exc.TransferAPIError)
    with pytest.raises(exc.GlobusTransferError):
        mock_cli.upload(EMPTY_TEST_FILE, 'my_folder')


def test_upload_with_custom_metadata(mock_cli):
    cust_meta = {'custom_key': 'custom_value'}
    stats = mock_cli.upload(EMPTY_TEST_FILE, 'my_folder', metadata=cust_meta)
    meta = stats['new_metadata']
    assert 'custom_key' in meta['project_metadata']
    assert meta['project_metadata']['custom_key'] == 'custom_value'


def test_upload_analyze_error(mock_cli, monkeypatch):
    mock_exc = Mock(side_effect=AnalysisException('fail!', None))
    monkeypatch.setattr(analysis, 'analyze_dataframe', mock_exc)
    with pytest.raises(exc.AnalysisException):
        mock_cli.upload(EMPTY_TEST_FILE, 'my_folder')


def test_upload_validation_error(mock_cli, mock_transfer_log):
    invalid_m = {'formats': [1234]}
    with pytest.raises(jsonschema.exceptions.ValidationError):
        mock_cli.upload(EMPTY_TEST_FILE, 'my_folder', metadata=invalid_m)


def test_no_update_needed(mock_cli, mock_transfer_log, mock_search_client):
    basen = os.path.basename(EMPTY_TEST_FILE)
    url = mock_cli.get_globus_http_url(basen)
    meta = scrape_metadata(EMPTY_TEST_FILE, url, mock_cli.profile,
                           'foo-project')
    entry = {'content': [meta], 'subject': mock_cli.get_subject_url(basen)}
    mock_cli.list_entries = Mock(return_value=[entry])
    mock_cli.upload(EMPTY_TEST_FILE, '/', update=True)
    assert not mock_search_client.ingest.called
    assert not mock_transfer_log.called


def test_upload_record_exists(mock_cli):
    url = mock_cli.get_globus_http_url('my_folder/test_file_zero_length.txt')
    sub = mock_cli.get_subject_url('my_folder')
    meta = scrape_metadata(EMPTY_TEST_FILE, url, mock_cli.profile, 'foo')
    entry = {'content': [meta], 'subject': sub}
    mock_cli.list_entries = Mock(return_value=[entry])
    with pytest.raises(exc.RecordExists):
        mock_cli.upload(SMALL_TEST_FILE, 'my_folder')


def test_upload_dry_run(mock_cli):
    stats = mock_cli.upload(SMALL_TEST_FILE, 'my_folder', dry_run=True)
    assert not stats['ingest']
    assert not stats['upload']
    assert stats['files_modified'] is True
    assert stats['metadata_modified'] is True
    assert stats['protocol'] == 'globus'
    assert stats['version'] is None
    assert stats['record_exists'] is False
    assert stats['new_version'] == '1'


def test_dataframe_up_to_date(mock_cli, mock_transfer_log, monkeypatch):
    """Update metadata but not the actual file"""
    sub = mock_cli.get_subject_url(os.path.basename(EMPTY_TEST_FILE))
    with open(EMTPY_TEST_FILE_META) as f:
        le = Mock(return_value=[
            {'content': [json.load(f)],
             'subject': sub}
        ])
        mock_cli.list_entries = le
    new_meta = {"custom_metadata_key": "custom_metadata_value"}
    res = mock_cli.upload(EMPTY_TEST_FILE, '/', metadata=new_meta, update=True)
    assert res['record_exists']
    assert res['metadata_modified'] is True
    assert res['files_modified'] is False
    assert not globus_sdk.TransferData.called


def test_upload_local_endpoint_not_set(mock_cli, mock_profile):

    mock_cli.profile.save_option('local_endpoint', None, section='profile')
    with pytest.raises(exc.NoLocalEndpointSet):
        mock_cli.upload(SMALL_TEST_FILE, 'my_folder', globus=True)


def test_upload_gcp_log(mock_cli, mock_transfer_log):
    mock_cli.get_full_search_entry.return_value = {}
    mock_cli.get_transfer_client().submit_transfer.return_value = {}
    mock_cli.upload(SMALL_TEST_FILE, 'my_folder', globus=True)
    assert mock_transfer_log.called

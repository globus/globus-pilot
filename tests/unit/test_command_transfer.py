import os
import json
from unittest.mock import Mock
from click.testing import CliRunner
import globus_sdk
from pilot.commands.transfer.transfer_commands import upload
from pilot import transfer_log
from pilot.search import scrape_metadata
from pilot import analysis
from pilot.exc import ExitCodes, AnalysisException
from tests.unit.mocks import COMMANDS_FILE_BASE_DIR

EMPTY_TEST_FILE = os.path.join(COMMANDS_FILE_BASE_DIR,
                               'test_file_zero_length.txt')
EMTPY_TEST_FILE_META = os.path.join(COMMANDS_FILE_BASE_DIR,
                                    'empty_file_metadata.json')
SMALL_TEST_FILE = os.path.join(COMMANDS_FILE_BASE_DIR, 'test_file_small.txt')
CUSTOM_METADATA = os.path.join(COMMANDS_FILE_BASE_DIR, 'custom_metadata.json')
INVALID_METADATA = os.path.join(COMMANDS_FILE_BASE_DIR,
                                'invalid_metadata.json')


def test_upload(mock_cli, monkeypatch):
    monkeypatch.setattr(transfer_log.TransferLog, 'add_log', Mock())
    result = CliRunner().invoke(upload, [EMPTY_TEST_FILE, 'my_folder'])
    assert result.exit_code == ExitCodes.SUCCESS


def test_upload_without_destination(mock_cli):
    mock_cli.ls.return_value = {'foo': {'type': 'dir'},
                                'bar': {'type': 'file'}}
    result = CliRunner().invoke(upload, [EMPTY_TEST_FILE])
    assert result.exit_code == ExitCodes.NO_DESTINATION_PROVIDED
    assert 'No Destination Provided' in result.output
    assert 'foo' in result.output
    assert 'bar' not in result.output


def test_upload_to_nonexistant_dir(mock_cli, mock_transfer_error):
    mock_transfer_error.code = 'ClientError.NotFound'
    mock_cli.ls = Mock(side_effect=globus_sdk.exc.TransferAPIError)
    result = CliRunner().invoke(upload, [EMPTY_TEST_FILE, 'my_folder'])
    assert result.exit_code == ExitCodes.DIRECTORY_DOES_NOT_EXIST


def test_upload_unexpected_ls_error(mock_cli, mock_transfer_error):
    mock_transfer_error.code = 'UnexpectedError'
    mock_cli.ls = Mock(side_effect=globus_sdk.exc.TransferAPIError)
    result = CliRunner().invoke(upload, [EMPTY_TEST_FILE, 'my_folder'])
    assert result.exit_code == ExitCodes.GLOBUS_TRANSFER_ERROR


def test_upload_with_custom_metadata(mock_cli):
    result = CliRunner().invoke(upload, [EMPTY_TEST_FILE, 'my_folder',
                                         '-j', CUSTOM_METADATA, '--verbose',
                                         '--dry-run'])
    assert result.exit_code == 0
    assert 'custom_metadata_key' in result.output
    assert 'custom_metadata_value' in result.output


def test_upload_analyze_error(mock_cli, monkeypatch):
    mock_exc = Mock(side_effect=AnalysisException('fail!', None))
    monkeypatch.setattr(analysis, 'analyze_dataframe', mock_exc)
    result = CliRunner().invoke(upload, [EMPTY_TEST_FILE, 'my_folder',
                                         '--no-gcp'])
    assert result.exit_code == 0
    assert 'Error analyzing' in result.output
    assert '(Use --verbose to see full error)' in result.output


def test_upload_validation_error(mock_cli):
    result = CliRunner().invoke(upload, [EMPTY_TEST_FILE, 'my_folder',
                                         '--no-gcp', '-j', INVALID_METADATA])
    print(result.output)
    assert result.exit_code == ExitCodes.INVALID_METADATA


def test_no_update_needed(mock_cli, mock_search_results):
    base_name = os.path.basename(EMPTY_TEST_FILE)
    url = mock_cli.get_globus_http_url(base_name)
    sub = mock_cli.get_subject_url(base_name)
    meta = scrape_metadata(EMPTY_TEST_FILE, url, mock_cli.profile,
                           'foo-project')
    mock_search_results['gmeta'][0]['content'][0] = meta
    mock_search_results['gmeta'][0]['subject'] = sub
    mock_cli.list_entries = Mock(return_value=mock_search_results['gmeta'])
    result = CliRunner().invoke(upload, [EMPTY_TEST_FILE, '/',
                                         '--no-gcp', '-u'])
    assert result.exit_code == 0
    assert 'Files and search entry are an exact match.' in result.output


def test_upload_record_exists(mock_cli, mock_search_results):
    base_name = os.path.basename(EMPTY_TEST_FILE)
    url = mock_cli.get_globus_http_url(base_name)
    sub = mock_cli.get_subject_url(base_name)
    meta = scrape_metadata(EMPTY_TEST_FILE, url, mock_cli.profile,
                           'foo-project')
    mock_search_results['gmeta'][0]['content'][0] = meta
    mock_search_results['gmeta'][0]['subject'] = sub
    mock_cli.list_entries = Mock(return_value=mock_search_results['gmeta'])

    result = CliRunner().invoke(upload, [EMPTY_TEST_FILE, '/', '--no-gcp'])
    assert result.exit_code == ExitCodes.RECORD_EXISTS


def test_upload_dry_run(mock_cli):
    result = CliRunner().invoke(upload, [SMALL_TEST_FILE, 'my_folder',
                                         '--verbose', '--dry-run'])
    assert result.exit_code == 0
    assert 'text/plain' in result.output


def test_dataframe_up_to_date(mock_cli, mock_transfer_log,
                              mock_search_results):
    with open(EMTPY_TEST_FILE_META) as f:
        meta = json.load(f)
    base_name = os.path.basename(EMPTY_TEST_FILE)
    sub = mock_cli.get_subject_url(base_name)
    mock_search_results['gmeta'][0]['content'][0] = meta
    mock_search_results['gmeta'][0]['subject'] = sub
    mock_cli.list_entries = Mock(return_value=mock_search_results['gmeta'])
    result = CliRunner().invoke(upload, [EMPTY_TEST_FILE, '/',
                                         '-u', '-j', CUSTOM_METADATA])
    assert result.exit_code == 0
    assert not globus_sdk.TransferData.called


def test_upload_local_endpoint_not_set(mock_cli, mock_profile):

    mock_cli.profile.save_option('local_endpoint', None, section='profile')
    result = CliRunner().invoke(upload, [SMALL_TEST_FILE, 'my_folder'
                                         '--gcp'])
    assert result.exit_code == ExitCodes.NO_LOCAL_ENDPOINT_SET


def test_upload_gcp_log(mock_cli, mock_transfer_log):
    mock_cli.get_transfer_client().submit_transfer.return_value = {}
    result = CliRunner().invoke(upload, [EMPTY_TEST_FILE, 'my_folder'])
    assert result.exit_code == 0
    assert mock_transfer_log.called

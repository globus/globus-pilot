import os
import pytest
import globus_sdk
from unittest.mock import Mock, call, mock_open, patch
from pilot import globus_clients, exc
from tests.unit.mocks import (MOCK_PROFILE, MOCK_TOKEN_SET,
                              CLIENT_FILE_BASE_DIR)
from fair_research_login.exc import LoadError

TINY_DATAFRAME = os.path.join(CLIENT_FILE_BASE_DIR, 'tiny_dataframe.tsv')


def test_login(monkeypatch, mock_cli_basic, mock_config):
    assert mock_config.load()['profile'] == {}
    auth_cli = Mock()
    monkeypatch.setattr(mock_cli_basic, 'get_auth_client',
                        Mock(return_value=auth_cli))
    mp = MOCK_PROFILE.copy()
    mp['name'] = 'Real Genius'
    auth_cli.oauth2_userinfo.return_value.data = mp
    mock_cli_basic.login()
    assert auth_cli.oauth2_userinfo.called
    assert mock_cli_basic.profile.name == mp['name']


def test_logout(monkeypatch, mock_cli_basic, mock_config):
    monkeypatch.setattr(mock_cli_basic, 'revoke_token_set', Mock())
    cfg = mock_config.load()
    cfg['tokens'] = MOCK_TOKEN_SET
    mock_cli_basic.logout()
    assert mock_config.load()['tokens'] == {}


def test_is_logged_in(monkeypatch, mock_cli_basic):
    load_tokens = Mock()
    monkeypatch.setattr(mock_cli_basic, 'load_tokens', load_tokens)

    load_tokens.return_value = {'a bunch ': 'of tokens'}
    assert mock_cli_basic.is_logged_in() is True

    load_tokens.side_effect = LoadError
    assert mock_cli_basic.is_logged_in() is False


def test_get_clients(mock_cli_basic):
    assert isinstance(mock_cli_basic.get_auth_client(), globus_sdk.AuthClient)
    assert isinstance(mock_cli_basic.get_transfer_client(),
                      globus_sdk.TransferClient)
    assert isinstance(mock_cli_basic.get_search_client(),
                      globus_sdk.SearchClient)


def test_ls(monkeypatch, mock_cli_basic):
    transfer_cli = Mock()
    transfer_cli.operation_ls.return_value = {
        'DATA': [{'type': 'file', 'name': 'one'},
                 {'type': 'dir', 'name': 'two'}]
    }
    monkeypatch.setattr(mock_cli_basic, 'get_transfer_client',
                        Mock(return_value=transfer_cli))
    result = mock_cli_basic.ls('foo')

    assert transfer_cli.operation_ls.called
    transfer_cli.operation_ls.assert_called_with('foo-project-endpoint',
                                                 path='/foo_folder/foo')
    # ensure only the file was returned
    assert len(result) == 2


def test_upload_http(monkeypatch, mixed_tsv, mock_cli_basic):
    put = Mock()
    monkeypatch.setattr(globus_clients.HTTPFileClient, 'put', put)
    mock_cli_basic.upload_http(TINY_DATAFRAME, 'destination')
    assert put.called
    assert put.call_args == call('/foo_folder/destination/tiny_dataframe.tsv',
                                 filename=TINY_DATAFRAME)


def test_download_http(monkeypatch, mixed_tsv, mock_cli_basic, mock_projects):
    response = Mock()
    response.iter_content = ['hello', 'world']
    get = Mock(return_value=response)
    monkeypatch.setattr(globus_clients.HTTPFileClient, 'get', get)
    monkeypatch.setattr(os, 'mkdir', Mock())
    m_open = mock_open()
    m_open.return_value.write.return_value = 1
    with patch("builtins.open", m_open):
        mock_cli_basic.download('a.tsv')
    assert get.called
    assert get.call_args == call('/foo_folder/a.tsv', range=None)


def test_ingest(monkeypatch, mock_cli_basic, mock_sdk_response):
    search_cli = Mock()
    search_cli.ingest.return_value = {'task_id': 'foo'}
    search_cli.get_task = Mock(return_value={'state': 'SUCCESS'})
    monkeypatch.setattr(mock_cli_basic, 'get_search_client',
                        Mock(return_value=search_cli))
    meta = mock_cli_basic.gather_metadata(TINY_DATAFRAME, '/')
    r = mock_cli_basic.ingest('tiny_dataframe.tsv', meta)
    assert r is True

    mock_sdk_response.data = {'state': 'FAILURE', 'message': 'it failed!'}
    search_cli.get_task.return_value = mock_sdk_response
    with pytest.raises(exc.PilotClientException):
        mock_cli_basic.ingest('tiny_dataframe.tsv', meta)


def test_get_search_entry(monkeypatch, mock_cli_basic):
    search_cli = Mock()
    search_cli.get_subject.return_value = {'content': ['myresult']}
    mock_cli_basic.get_search_client = Mock(return_value=search_cli)

    assert mock_cli_basic.get_search_entry('foo') == 'myresult'
    search_cli.get_subject.assert_called_with(
        'foo-search-index',
        'globus://foo-project-endpoint/foo_folder/foo',
        result_format_version='2017-09-01',
    )

    class MockException(Exception):
        code = 'random_exception.generic'

    monkeypatch.setattr(globus_sdk.exc, 'SearchAPIError', MockException)
    search_cli.get_subject.side_effect = globus_sdk.exc.SearchAPIError
    assert mock_cli_basic.get_search_entry('foo') is None


def test_list_entries(mock_multi_file_result, mock_cli_basic):
    results = mock_multi_file_result.copy()
    mfr = mock_multi_file_result['gmeta'][0]
    ent2 = mfr.copy()
    ent2['subject'] = 'globus://foo-project-endpoint/foo_folder/foo/bar/moo'
    ent3 = mfr.copy()
    ent3['subject'] = 'globus://foo-project-endpoint/foo_folder/foo/bar/baz'
    results['gmeta'] = [mfr, ent2, ent3]
    ps_response = Mock()
    ps_response.data = results
    search_cli = Mock()
    mock_cli_basic.get_search_client = Mock(return_value=search_cli)
    search_cli.post_search.return_value = ps_response

    assert len(mock_cli_basic.list_entries('')) == 3
    assert len(mock_cli_basic.list_entries('foo/bar')) == 2
    assert len(mock_cli_basic.list_entries('foo/bar/moo')) == 1
    assert len(mock_cli_basic.list_entries('foo/bar/baz')) == 1
    assert len(mock_cli_basic.list_entries('foo/foo/foo')) == 0


def test_get_search_entry_dir(monkeypatch, mock_cli_basic,
                              mock_multi_file_result):
    search_cli = Mock()
    mock_cli_basic.get_search_client = Mock(return_value=search_cli)

    class MockException(Exception):
        code = 'NotFound.Generic'

    monkeypatch.setattr(globus_sdk.exc, 'SearchAPIError', MockException)
    search_cli.get_subject.side_effect = globus_sdk.exc.SearchAPIError
    ps_response = Mock()
    ps_response.data = mock_multi_file_result
    search_cli.post_search.return_value = ps_response
    entry = mock_cli_basic.get_search_entry('multi_file/text_metadata.txt')
    assert entry == mock_multi_file_result['gmeta'][0]['content'][0]


def test_delete_entry_sub(monkeypatch, mock_cli_basic, mock_multi_file_result):
    search_cli = Mock()
    mock_cli_basic.ingest_entry = Mock()
    monkeypatch.setattr(mock_cli_basic, 'get_search_client',
                        Mock(return_value=search_cli))
    ment = Mock(return_value=mock_multi_file_result['gmeta'][0])
    mock_cli_basic.get_full_search_entry = ment
    mock_cli_basic.delete_entry('/multi_file', entry_id='my_id')
    assert not mock_cli_basic.ingest_entry.called
    assert search_cli.delete_entry.call_args == call(
        'foo-search-index',
        'globus://foo-project-endpoint/foo_folder/multi_file',
        entry_id='my_id'
    )
    mock_cli_basic.delete_entry('/multi_file', 'my_custom_id',
                                full_subject=True)
    assert search_cli.delete_subject.called


def test_delete_file_in_mfe(mock_cli_basic, mock_search_client,
                            mock_multi_file_result):
    mock_cli_basic.ingest = Mock()
    mock_cli_basic.get_full_search_entry = Mock(
        return_value=mock_multi_file_result['gmeta'][0])
    mock_cli_basic.delete_entry('/multi_file/text_metadata.txt')
    assert mock_cli_basic.ingest.called


def test_delete_entry_no_result(monkeypatch, mock_cli_basic):
    search_cli = Mock()
    monkeypatch.setattr(mock_cli_basic, 'get_search_client',
                        Mock(return_value=search_cli))
    mock_cli_basic.get_full_search_entry = Mock(return_value=None)
    with pytest.raises(exc.RecordDoesNotExist):
        mock_cli_basic.delete_entry('foo', 'bar')


def test_delete_file(mock_cli_basic, mock_transfer_client):
    mock_cli_basic.delete('foo.txt')
    assert mock_transfer_client.submit_delete.called


def test_delete_multifile_entry(mock_cli_basic, mock_transfer_client):
    mock_cli_basic.delete('foo/', recursive=True)
    assert mock_transfer_client.submit_delete.called


def test_delete_will_not_delete_base_dir(mock_cli_basic,
                                         mock_transfer_client):
    with pytest.raises(exc.DataOutsideProject):
        mock_cli_basic.delete('/', recursive=True)


def test_delete_will_not_delete_above_base_dir(mock_cli_basic,
                                               mock_transfer_client):
    with pytest.raises(exc.DataOutsideProject):
        mock_cli_basic.delete('/', recursive=True, relative=False)

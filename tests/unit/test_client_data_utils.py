import pytest
import globus_sdk
from unittest.mock import Mock, call
from pilot.client import PilotClient
from pilot import globus_clients, exc
from tests.unit.mocks import MOCK_PROFILE, MOCK_TOKEN_SET
from fair_research_login.exc import LoadError


@pytest.mark.skip
def test_upload_gcp(mock_transfer_client, mixed_tsv, mock_config):
    pc = PilotClient()
    result = pc.upload_gcp(mixed_tsv, 'bar', test=True)
    assert result.data['code'] == 'Accepted'


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
    assert len(result) == 1


def test_upload_http(monkeypatch, mixed_tsv, mock_cli_basic):
    put = Mock()
    monkeypatch.setattr(globus_clients.HTTPSClient, 'put', put)
    mock_cli_basic.upload('a.tsv', 'destination')
    assert put.called
    assert put.call_args == call('/foo_folder/destination', filename='a.tsv')


def test_ingest(monkeypatch, mock_cli_basic):
    search_cli = Mock()
    search_cli.ingest.return_value = {'task_id': 'foo'}
    search_cli.get_task = Mock(return_value={'state': 'SUCCESS'})
    monkeypatch.setattr(mock_cli_basic, 'get_search_client',
                        Mock(return_value=search_cli))
    r = mock_cli_basic.ingest_entry({'my': 'search_entry'})
    assert r is True

    search_cli.get_task = Mock(return_value={'state': 'FAILURE'})
    with pytest.raises(exc.PilotClientException):
        mock_cli_basic.ingest_entry({'my': 'search_entry'})


def test_get_search_entry(monkeypatch, mock_cli_basic):
    search_cli = Mock()
    search_cli.get_subject.return_value = {'content': ['myresult']}
    monkeypatch.setattr(mock_cli_basic, 'get_search_client',
                        Mock(return_value=search_cli))
    assert mock_cli_basic.get_search_entry('foo') == 'myresult'
    search_cli.get_subject.assert_called_with(
        'foo-search-index',
        'globus://foo-project-endpoint/foo_folder/foo'
    )

    class MockException(Exception):
        pass

    monkeypatch.setattr(globus_sdk.exc, 'SearchAPIError', MockException)
    search_cli.get_subject.side_effect = globus_sdk.exc.SearchAPIError
    assert mock_cli_basic.get_search_entry('foo') is None


def test_delete_entry(monkeypatch, mock_cli_basic):
    search_cli = Mock()
    monkeypatch.setattr(mock_cli_basic, 'get_search_client',
                        Mock(return_value=search_cli))
    mock_cli_basic.delete_entry('foo', 'bar')
    assert search_cli.delete_entry.called


def test_delete_subject(monkeypatch, mock_cli_basic):
    search_cli = Mock()
    monkeypatch.setattr(mock_cli_basic, 'get_search_client',
                        Mock(return_value=search_cli))
    mock_cli_basic.delete_entry('foo', 'bar', full_subject=True)
    assert search_cli.delete_subject.called

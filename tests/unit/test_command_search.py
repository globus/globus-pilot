from unittest.mock import Mock
import globus_sdk
from click.testing import CliRunner
from pilot.commands.search.search_commands import list_command, describe


def test_list_command(monkeypatch, mock_cli, mock_search_results):
    sc = Mock()
    sc.search.return_value = mock_search_results
    monkeypatch.setattr(globus_sdk, 'SearchClient', Mock(return_value=sc))
    runner = CliRunner()
    result = runner.invoke(list_command, [])
    assert result.exit_code == 0


def test_upload_gcp_log(mock_cli, mock_search_result):
    mock_cli.get_search_entry.return_value = mock_search_result['content'][0]
    runner = CliRunner()
    result = runner.invoke(describe, ['foo/bar'])
    assert result.exit_code == 0

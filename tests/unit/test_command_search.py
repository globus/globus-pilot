from unittest.mock import Mock
from click.testing import CliRunner
from pilot.commands.search.search_commands import list_command, describe


def test_list_command(monkeypatch, mock_cli, mock_search_results):
    sc = Mock()
    globus_response = Mock()
    globus_response.data = mock_search_results
    sc.post_search.return_value = globus_response
    mock_cli.get_search_client = Mock(return_value=sc)
    assert sc.post_search().data == mock_search_results

    runner = CliRunner()
    result = runner.invoke(list_command, [])
    assert result.exit_code == 0


def test_upload_gcp_log(mock_cli, mock_search_result):
    mock_cli.get_search_entry.return_value = mock_search_result['content'][0]
    runner = CliRunner()
    result = runner.invoke(describe, ['foo/bar'])
    assert result.exit_code == 0

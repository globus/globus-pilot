from click.testing import CliRunner
from pilot.commands.search.search_commands import list_command, describe


def test_list_command(monkeypatch, mock_cli, mock_search_results):
    mock_cli.search.return_value = mock_search_results
    mock_cli.ls.return_value = {}
    runner = CliRunner()
    result = runner.invoke(list_command, [])
    assert result.exit_code == 0


def test_upload_gcp_log(mock_cli, mock_search_result):
    mock_cli.get_full_search_entry.return_value = mock_search_result
    runner = CliRunner()
    result = runner.invoke(describe, ['foo/bar'])
    assert result.exit_code == 0

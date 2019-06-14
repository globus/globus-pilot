from click.testing import CliRunner
from pilot.commands.search.delete import delete_command


def test_delete(mock_cli):
    runner = CliRunner()
    result = runner.invoke(delete_command, ['foo/bar'])
    assert result.exit_code == 0
    assert mock_cli.delete_entry.called

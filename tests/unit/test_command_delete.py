from click.testing import CliRunner
from pilot.commands.search.delete import delete_command


def test_delete(mock_command_pilot_cli):
    runner = CliRunner()
    result = runner.invoke(delete_command, ['foo/bar'])
    print(mock_command_pilot_cli.delete_entry)
    assert result.exit_code == 0
    assert mock_command_pilot_cli.delete_entry.called

from click.testing import CliRunner
from pilot.commands.search.delete import delete_command


def test_delete(mock_cli):
    runner = CliRunner()
    mock_cli.ls.return_value = {'bar': {'type': 'file'}}
    result = runner.invoke(delete_command, ['foo/bar'])
    assert result.exit_code == 0
    assert mock_cli.delete_entry.called

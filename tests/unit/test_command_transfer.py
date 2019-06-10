import os
from unittest.mock import Mock
from click.testing import CliRunner
from pilot.commands.transfer.transfer_commands import upload
from tests.unit.mocks import COMMANDS_FILE_BASE_DIR


def test_upload(mock_command_pilot_cli, mock_config):
    test_file = os.path.join(COMMANDS_FILE_BASE_DIR,
                             'test_file_zero_length.txt')
    m_file = os.path.join(COMMANDS_FILE_BASE_DIR,
                          'test_command_upload_minimal.json')
    upload_response = Mock()
    upload_response.status_code = 200
    mock_command_pilot_cli.upload.return_value = upload_response
    mock_command_pilot_cli.get_search_entry.return_value = None
    runner = CliRunner()
    result = runner.invoke(upload, [test_file, 'my_folder', '--no-gcp',
                                    '-j', m_file,
                                    '--no-analyze'])
    assert result.exit_code == 0


def test_upload_gcp_log(mock_command_pilot_cli, mock_config):
    test_file = os.path.join(COMMANDS_FILE_BASE_DIR,
                             'test_file_zero_length.txt')
    m_file = os.path.join(COMMANDS_FILE_BASE_DIR,
                          'test_command_upload_minimal.json')
    mock_command_pilot_cli.get_search_entry.return_value = None
    runner = CliRunner()
    result = runner.invoke(upload, [test_file, 'my_folder', '--gcp',
                                    '-j', m_file,
                                    '--no-analyze'])
    assert result.exit_code == 0

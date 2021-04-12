import os
from unittest.mock import Mock
from click.testing import CliRunner
from pilot.commands.auth.auth_commands import (
    login, logout, profile_command)


def test_auth_login(monkeypatch, mock_cli, mock_config, mock_transfer_client,
                    mock_sdk_response):
    monkeypatch.setattr(mock_cli, 'is_logged_in', Mock(return_value=False))
    mock_sdk_response.data = {'display_name': 'my_computer'}
    mock_transfer_client.get_endpoint.return_value = mock_sdk_response
    runner = CliRunner()
    result = runner.invoke(login, [])
    assert result.exit_code == 0
    assert mock_cli.login.called


def test_auth_logout(mock_cli):
    runner = CliRunner()
    result = runner.invoke(logout, [])
    assert result.exit_code == 0
    assert mock_cli.logout.called


def test_auth_logout_purge(monkeypatch, mock_cli):
    monkeypatch.setattr(os, 'unlink', Mock())
    monkeypatch.setattr(os.path, 'exists', Mock(return_value=True))
    runner = CliRunner()
    result = runner.invoke(logout, ['--purge'])
    assert result.exit_code == 0
    assert mock_cli.logout.called
    assert os.unlink.called


def test_auth_profile(mock_cli, mock_config):
    runner = CliRunner()
    result = runner.invoke(profile_command, [])
    assert result.exit_code == 0

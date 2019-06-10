import os
from unittest.mock import Mock
from click.testing import CliRunner
from pilot.commands.auth.auth_commands import (
    login, logout, whoami, profile_command)



def test_auth_login(monkeypatch, mock_command_pilot_cli, mock_profile):
    mock_command_pilot_cli.token_storage.tokens = {}
    is_logged_in = Mock(return_value=False)
    monkeypatch.setattr(mock_command_pilot_cli, 'is_logged_in', is_logged_in)
    runner = CliRunner()
    result = runner.invoke(login, [])
    assert result.exit_code == 0
    assert mock_command_pilot_cli.login.called


def test_auth_logout(mock_command_pilot_cli):
    runner = CliRunner()
    result = runner.invoke(logout, [])
    assert result.exit_code == 0
    assert mock_command_pilot_cli.logout.called


def test_auth_logout_purge(monkeypatch, mock_command_pilot_cli):
    monkeypatch.setattr(os, 'unlink', Mock())
    runner = CliRunner()
    result = runner.invoke(logout, ['--purge'])
    assert result.exit_code == 0
    assert mock_command_pilot_cli.logout.called
    assert os.unlink.called


def test_auth_whoami(mock_command_pilot_cli, mock_profile):
    runner = CliRunner()
    result = runner.invoke(whoami, [])
    assert 'franklinr@globusid.org' in result.output
    assert result.exit_code == 0


def test_auth_profile(mock_command_pilot_cli, mock_config):
    runner = CliRunner()
    result = runner.invoke(profile_command, [])
    assert result.exit_code == 0

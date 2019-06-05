import os
from unittest.mock import Mock
from click.testing import CliRunner
from pilot.commands.auth.auth_commands import (
    login, logout, whoami, profile_command)



def test_auth_login(mock_command_pilot_cli):
    mock_command_pilot_cli.token_storage.tokens = {}
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


def test_auth_profile(mock_command_pilot_cli, mock_config):
    runner = CliRunner()
    result = runner.invoke(profile_command, [])
    assert result.exit_code == 0

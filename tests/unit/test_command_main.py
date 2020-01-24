import globus_sdk
from unittest.mock import Mock
from click.testing import CliRunner

from pilot.commands.main import cli
from pilot import version


def test_main_no_config(monkeypatch, mock_cli, mock_config):
    mock_cli.config = mock_config
    monkeypatch.setattr(mock_cli, 'is_logged_in', Mock(return_value=False))
    migrate = Mock()
    monkeypatch.setattr(mock_cli.config, 'migrate', migrate)
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert 'Usage' in result.output
    assert result.exit_code == 0
    assert not migrate.called


def test_main_notify_update(monkeypatch, mock_cli):
    is_cache_stale = Mock(return_value=True)
    monkeypatch.setattr(mock_cli.context, 'is_cache_stale', is_cache_stale)
    update_with_diff = Mock(return_value={'added': 'stuff'})
    monkeypatch.setattr(mock_cli.context, 'update_with_diff', update_with_diff)

    runner = CliRunner()
    runner.invoke(cli, [])
    assert is_cache_stale.called
    assert update_with_diff.called


def test_main_warns_no_project_set(monkeypatch, mock_cli):
    # Ensures we don't call update and try to load tokens
    monkeypatch.setattr(mock_cli.context, 'is_cache_stale',
                        Mock(return_value=False))
    is_set = Mock(return_value=False)
    monkeypatch.setattr(mock_cli.project, 'is_set', is_set)

    runner = CliRunner()
    result = runner.invoke(cli, ['list'])
    assert is_set.called
    assert 'No project set' in result.output


def test_main_error_fetching_projects(monkeypatch, mock_cli,
                                      mock_globus_exception):
    is_cache_stale = Mock(return_value=True)
    monkeypatch.setattr(mock_cli.context, 'is_cache_stale', is_cache_stale)

    monkeypatch.setattr(globus_sdk.exc, 'SearchAPIError',
                        mock_globus_exception)
    err = Mock(side_effect=mock_globus_exception)
    monkeypatch.setattr(mock_cli.context, 'update_with_diff', err)

    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert 'No manifest exists on this index.' in result.output


def test_main_migrate(monkeypatch, mock_cli):
    monkeypatch.setattr(mock_cli.config, 'is_migrated',
                        Mock(return_value=False))
    migrate = Mock()
    monkeypatch.setattr(mock_cli.config, 'migrate', migrate)

    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert migrate.called
    assert 'Old config detected, upgrading... Success!' in result.output


def test_main_migration_failure(monkeypatch, mock_cli):
    monkeypatch.setattr(mock_cli.config, 'is_migrated',
                        Mock(return_value=False))

    migrate = Mock(side_effect=Exception)
    monkeypatch.setattr(mock_cli.config, 'migrate', migrate)

    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert migrate.called
    assert 'Old config detected, upgrading... Failed!' in result.output


def test_main_version(monkeypatch, mock_cli):
    monkeypatch.setattr(mock_cli, 'is_logged_in', Mock(return_value=False))
    runner = CliRunner()
    result = runner.invoke(cli, ['version'])
    assert version.__version__ in result.output

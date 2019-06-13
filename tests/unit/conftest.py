import pytest
from configobj import ConfigObj
import os
import json
import copy
import globus_sdk
from unittest.mock import Mock
from .mocks import (MemoryStorage, MOCK_TOKEN_SET, GlobusTransferTaskResponse,
                    ANALYSIS_FILE_BASE_DIR, CLIENT_FILE_BASE_DIR,
                    MOCK_PROFILE, MOCK_PROJECTS)

from pilot import client, config, commands


@pytest.fixture
def mem_storage():
    return MemoryStorage()


@pytest.fixture
def mock_tokens():
    return copy.deepcopy(MOCK_TOKEN_SET)


@pytest.fixture
def mock_config(monkeypatch):
    class MockConfig:
        cfg = ConfigObj()

        def save(self, cfg):
            self.cfg = cfg

        def load(self):
            return self.cfg

    mock_cfg = MockConfig()
    monkeypatch.setattr(config.Config, 'load', mock_cfg.load)
    monkeypatch.setattr(config.Config, 'save', mock_cfg.save)
    return config.Config()


@pytest.fixture
def mock_profile(mock_config):
    cfg = mock_config.load()
    cfg['profile'] = MOCK_PROFILE
    mock_config.save(cfg)
    return mock_config


@pytest.fixture
def mock_projects(mock_config):
    cfg = mock_config.load()
    cfg['projects'] = MOCK_PROJECTS
    mock_config.save(cfg)
    return mock_config


@pytest.fixture
def mixed_tsv():
    return os.path.join(ANALYSIS_FILE_BASE_DIR, 'mixed.tsv')


@pytest.fixture
def numbers_tsv():
    return os.path.join(ANALYSIS_FILE_BASE_DIR, 'numbers.tsv')


@pytest.fixture
def mock_transfer_client(monkeypatch):
    st = Mock()
    monkeypatch.setattr(globus_sdk.TransferClient, 'submit_transfer', st)
    st.return_value = GlobusTransferTaskResponse()
    monkeypatch.setattr(globus_sdk, 'TransferData', Mock())
    return st


@pytest.fixture
def mock_auth_pilot_cli(monkeypatch, mock_transfer_client, mock_profile,
                        mock_config, mock_projects):
    """
    Returns a mock logged in pilot client. Storage is mocked with a custom
    object, so this does behave slightly differently than the real client.
    All methods that reach out to remote resources are mocked, you need to
    re-mock them to return the test data you want.
    """
    pc = client.PilotClient()

    def load_tokens(*args, **kwargs):
        return MOCK_TOKEN_SET

    monkeypatch.setattr(pc, 'load_tokens', load_tokens)

    pc.config = mock_config
    pc.profile.config = mock_config
    pc.project.config = mock_config
    pc.project.current = 'foo-project'
    pc.upload = Mock()
    pc.login = Mock()
    pc.logout = Mock()
    pc.ingest_entry = Mock()
    pc.get_search_entry = Mock(return_value=None)
    pc.ls = Mock()
    pc.delete_entry = Mock()
    # Sanity. This *should* always return True, but will fail if we update
    # tokens at a later time.
    assert pc.is_logged_in()
    return pc


@pytest.fixture
def mock_command_pilot_cli(mock_auth_pilot_cli, monkeypatch):
    mock_func = Mock()
    mock_func.return_value = mock_auth_pilot_cli
    monkeypatch.setattr(commands, 'get_pilot_client', mock_func)
    return mock_auth_pilot_cli


@pytest.fixture
def mock_pc_existing_search_entry(mock_auth_pilot_cli):
    fname = os.path.join(CLIENT_FILE_BASE_DIR, 'search_entry_v1.json')
    with open(fname) as fh:
        entry_json = json.load(fh)
    print(entry_json)
    mock_auth_pilot_cli.get_search_entry.return_value = entry_json
    return mock_auth_pilot_cli

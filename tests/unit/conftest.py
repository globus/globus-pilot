import pytest
from configobj import ConfigObj
import os
import json
import copy
import globus_sdk
from unittest.mock import Mock
from .mocks import (MemoryStorage, MOCK_TOKEN_SET, GlobusTransferTaskResponse,
                    ANALYSIS_FILE_BASE_DIR, SCHEMA_FILE_BASE_DIR,
                    MOCK_PROFILE, MOCK_PROJECTS, MOCK_CONTEXT)

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
def mock_context(mock_config):
    cfg = mock_config.load()
    cfg['contexts'] = MOCK_CONTEXT
    cfg['context'] = {'current': list(MOCK_CONTEXT.keys())[0]}
    mock_config.save(cfg)
    return mock_config


@pytest.fixture
def mixed_tsv():
    return os.path.join(ANALYSIS_FILE_BASE_DIR, 'mixed.tsv')


@pytest.fixture
def numbers_tsv():
    return os.path.join(ANALYSIS_FILE_BASE_DIR, 'numbers.tsv')


@pytest.fixture
def mock_search_data():
    fname = os.path.join(SCHEMA_FILE_BASE_DIR, 'dataset', 'valid-typical.json')
    with open(fname) as fh:
        return json.load(fh)


@pytest.fixture
def mock_search_results(mock_search_data):
    return {'@datatype': 'GSearchResult', '@version': '2017-09-01', 'count': 1,
            'gmeta': [{'@datatype': 'GMetaResult', '@version': '2017-09-01',
                       'content': [mock_search_data],
                       'subject': 'foo_folder'}],
            'offset': 0, 'total': 1}


@pytest.fixture
def mock_search_result(mock_search_results):
    return mock_search_results['gmeta'][0]


@pytest.fixture
def mock_transfer_client(monkeypatch):
    st = Mock()
    monkeypatch.setattr(globus_sdk.TransferClient, 'submit_transfer', st)
    st.return_value = GlobusTransferTaskResponse()
    monkeypatch.setattr(globus_sdk, 'TransferData', Mock())
    return st


@pytest.fixture
def mock_transfer_error(monkeypatch):
    class MockError(Exception):
        code = 'Error'
        message = 'A Globus SDK Transfer Error occurred! (Mock)'

    monkeypatch.setattr(globus_sdk.exc, 'TransferAPIError', MockError)
    return MockError


@pytest.fixture
def mock_cli_basic(monkeypatch, mock_config, mock_projects):
    pc = client.PilotClient()

    def load_tokens(*args, **kwargs):
        return MOCK_TOKEN_SET

    monkeypatch.setattr(pc, 'load_tokens', load_tokens)
    monkeypatch.setattr(commands, 'get_pilot_client', Mock(return_value=pc))
    monkeypatch.setattr(pc, 'config', mock_config)
    pc.config = mock_config
    pc.profile.config = mock_config
    pc.project.config = mock_config
    pc.project.current = 'foo-project'
    # Sanity. This *should* always return True, but will fail if we update
    # tokens at a later time.
    assert pc.is_logged_in()
    return pc


@pytest.fixture
def mock_cli(mock_cli_basic, mock_transfer_client, mock_profile):
    """
    Returns a mock logged in pilot client. Storage is mocked with a custom
    object, so this does behave slightly differently than the real client.
    All methods that reach out to remote resources are mocked, you need to
    re-mock them to return the test data you want.
    """
    mock_cli_basic.upload = Mock()
    mock_cli_basic.login = Mock()
    mock_cli_basic.logout = Mock()
    mock_cli_basic.ingest_entry = Mock()
    mock_cli_basic.get_search_entry = Mock(return_value=None)
    mock_cli_basic.ls = Mock()
    mock_cli_basic.mkdir = Mock()
    mock_cli_basic.delete = Mock()
    mock_cli_basic.delete_entry = Mock()
    mock_cli_basic.get_search_client = Mock()
    mock_cli_basic.get_transfer_client = Mock()
    mock_cli_basic.get_auth_client = Mock()
    return mock_cli_basic

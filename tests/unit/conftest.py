import pytest
from configobj import ConfigObj
import os
import json
import copy
import time
import globus_sdk
from unittest.mock import Mock
from .mocks import (MemoryStorage, MOCK_TOKEN_SET, GlobusTransferTaskResponse,
                    GlobusResponse,
                    ANALYSIS_FILE_BASE_DIR, SCHEMA_FILE_BASE_DIR,
                    CLIENT_FILE_BASE_DIR,
                    MOCK_PROFILE, MOCK_PROJECTS, MOCK_CONTEXT)

from pilot import client, config, commands, transfer_log


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
    return config.Config('/tmp/test_pilot.cfg')


@pytest.fixture
def mock_profile(mock_config):
    cfg = mock_config.load()
    cfg['profile'] = MOCK_PROFILE
    mock_config.save(cfg)
    return mock_config


@pytest.fixture
def mock_projects(mock_config, mock_contexts):
    cfg = mock_config.load()
    cfg['projects'] = MOCK_PROJECTS
    mock_config.save(cfg)
    return mock_config


@pytest.fixture
def mock_contexts(mock_config):
    cfg = mock_config.load()
    cfg['contexts'] = MOCK_CONTEXT
    cfg['context'] = {'current': 'test-context', 'last_updated': time.time()}
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
def mock_multi_file_result(mock_search_results):
    data = mock_search_results.copy()
    mf_filename = os.path.join(CLIENT_FILE_BASE_DIR, 'multi_file_entry.json')
    with open(mf_filename) as f:
        multi_file = json.load(f)
    sub = 'globus://foo-project-endpoint/foo_folder/multi_file'
    data['gmeta'] = [{'content': [multi_file], 'subject': sub}]
    return data


@pytest.fixture
def mock_search_result(mock_search_results):
    return mock_search_results['gmeta'][0]


@pytest.fixture
def mock_transfer_data(monkeypatch):
    td = Mock()
    monkeypatch.setattr(globus_sdk, 'TransferData', Mock(return_value=td))
    return td


@pytest.fixture
def mock_transfer_client(monkeypatch, mock_transfer_data):
    tc = Mock()
    monkeypatch.setattr(globus_sdk, 'TransferClient', Mock(return_value=tc))
    tc.submit_transfer.return_value = GlobusTransferTaskResponse()
    monkeypatch.setattr(globus_sdk, 'DeleteData', Mock())
    return tc


@pytest.fixture
def mock_search_client(monkeypatch):
    sc = Mock()
    gr = GlobusResponse()
    gr.data = {'state': 'SUCCESS', 'message': 'a thing has been ingested'}
    sc.get_task.return_value = gr
    sc.ingest.return_value = {'task_id': 'mock_task_id'}
    monkeypatch.setattr(globus_sdk, 'SearchClient', Mock(return_value=sc))
    return sc


@pytest.fixture
def mock_globus_exception():
    class MockExc(Exception):
        code = 'Error'
        message = 'A Globus SDK Transfer Error occurred! (Mock)'
    return MockExc


@pytest.fixture
def mock_transfer_error(monkeypatch, mock_globus_exception):
    monkeypatch.setattr(globus_sdk.exc, 'TransferAPIError',
                        mock_globus_exception)
    return mock_globus_exception


@pytest.fixture
def mock_sdk_response():
    return GlobusResponse()


@pytest.fixture
def mock_cli_basic(monkeypatch, mock_config, mock_projects, mock_contexts):
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
def mock_transfer_log(monkeypatch):
    add_log = Mock()
    monkeypatch.setattr(transfer_log.TransferLog, 'add_log', add_log)
    return add_log


@pytest.fixture
def mock_cli(mock_cli_basic, mock_transfer_client, mock_search_client,
             mock_profile, mock_transfer_log):
    """
    Returns a mock logged in pilot client. Storage is mocked with a custom
    object, so this does behave slightly differently than the real client.
    All methods that reach out to remote resources are mocked, you need to
    re-mock them to return the test data you want.
    """
    mock_cli_basic.transfer_file = Mock()
    mock_cli_basic.login = Mock()
    mock_cli_basic.logout = Mock()
    mock_cli_basic.get_full_search_entry = Mock(return_value=None)
    mock_cli_basic.search = Mock(return_value={'gmeta': []})
    mock_cli_basic.ls = Mock()
    mock_cli_basic.mkdir = Mock()
    mock_cli_basic.delete = Mock()
    mock_cli_basic.delete_entry = Mock()
    mock_cli_basic.get_auth_client = Mock()
    mock_cli_basic.get_http_client = Mock()
    return mock_cli_basic


@pytest.fixture
def mock_paths(mock_cli):
    short_path = 'test_path'
    return {
        'short_path': short_path,
        'full_path': mock_cli.get_path(short_path),
        'subject': mock_cli.get_subject_url(short_path),
        'http': mock_cli.get_globus_http_url(short_path),
    }

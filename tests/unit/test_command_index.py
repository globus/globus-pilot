import copy
import uuid
from click.testing import CliRunner
from tests.unit.mocks import MOCK_INDEX_RECORD, GlobusResponse
from pilot.commands.project.index import set_index, info


def test_set_index_with_prev_fetched_index(monkeypatch, mock_cli, mock_config,
                                           mock_search_client,
                                           mock_search_result):
    # Result when pilot context calls get_subject on the manifest record
    manifest = copy.deepcopy(mock_search_result)
    # This should be removed when we upgrade to the newer style search results
    manifest.pop('content')
    manifest['entries'] = [{'content': MOCK_INDEX_RECORD}]

    sub_resp = GlobusResponse()
    sub_resp.data = manifest
    mock_search_client.get_subject.return_value = sub_resp

    # Result when pilot fetches the general index_data
    index_resp = GlobusResponse()
    index_resp.data = {'display_name': 'foo'}
    mock_search_client.get_index.return_value = index_resp

    runner = CliRunner()
    result = runner.invoke(set_index, ['test-context'])
    assert result.exit_code == 0
    assert mock_search_client.get_subject.called
    assert mock_search_client.get_subject


def test_set_index_with_non_uuid(mock_cli):
    runner = CliRunner()
    result = runner.invoke(set_index, ['foo'])
    assert result.exit_code != 0
    assert 'must be a UUID' in result.output


def test_set_index_with_new_index(monkeypatch, mock_cli, mock_config,
                                  mock_search_client,
                                  mock_search_result):
    # Result when pilot context calls get_subject on the manifest record
    manifest = copy.deepcopy(mock_search_result)
    manifest.pop('content')
    manifest['entries'] = [{'content': MOCK_INDEX_RECORD}]
    sub_resp = GlobusResponse()
    sub_resp.data = manifest
    mock_search_client.get_subject.return_value = sub_resp

    # Result when pilot fetches the general index_data
    index_resp = GlobusResponse()
    index_resp.data = {'display_name': 'foo'}
    mock_search_client.get_index.return_value = index_resp

    # make a fake index
    fake_index = str(uuid.uuid4())

    runner = CliRunner()
    result = runner.invoke(set_index, [fake_index])
    assert result.exit_code == 0


def test_get_info(mock_cli):
    runner = CliRunner()
    result = runner.invoke(info, ['test-context'])
    assert result.exit_code == 0

from copy import deepcopy
from tests.unit.mocks import MOCK_PROJECTS


def test_get_diff(mock_cli):
    other_mock_projects = deepcopy(MOCK_PROJECTS)
    del other_mock_projects['bar-project']

    diff = mock_cli.context.get_diff(other_mock_projects, MOCK_PROJECTS)
    assert set(diff.keys()) == {'added'}
    assert 'bar-project' in diff['added']

    diff = mock_cli.context.get_diff(MOCK_PROJECTS, other_mock_projects)
    assert set(diff.keys()) == {'removed'}
    assert 'bar-project' in diff['removed']

    other_mock_projects['foo-project']['title'] = 'FOOOOOOO'
    diff = mock_cli.context.get_diff(MOCK_PROJECTS, other_mock_projects)
    assert set(diff.keys()) == {'changed', 'removed'}
    assert 'bar-project' in diff['removed']
    from pprint import pprint
    pprint(MOCK_PROJECTS)
    pprint(other_mock_projects)
    assert diff['changed'] == {'foo-project': {'title': 'Foo --> FOOOOOOO'}}

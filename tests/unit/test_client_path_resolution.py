import pytest
from urllib.parse import urlparse
from pilot.client import PilotClient
from pilot.exc import PilotInvalidProject

from tests.unit.mocks import MOCK_PROJECTS


def test_get_index(mock_projects):
    pc = PilotClient()
    pc.project.current = 'foo-project'
    assert pc.get_index() == 'foo-search-index'
    assert pc.get_index(project='foo-project-test') == 'foo-test-search-index'


def test_invalid_project(mock_projects):
    pc = PilotClient()
    with pytest.raises(PilotInvalidProject):
        pc.get_index()


def test_invalid_project_with_explicit_name(mock_projects):
    pc = PilotClient()
    with pytest.raises(PilotInvalidProject):
        pc.get_index('does-not-exist')


def test_get_path(mock_projects):
    pc = PilotClient()
    pc.project.current = 'foo-project'
    assert pc.get_path('folder/file.txt') == '/foo_folder/folder/file.txt'
    path = pc.get_path('folder/file.txt', project='foo-project-test')
    assert path == '/foo_test_folder/folder/file.txt'


def test_special_paths(mock_projects):
    pc = PilotClient()
    pc.project.current = 'foo-project'
    assert pc.get_path('///') == '/foo_folder'
    assert pc.get_path('.') == '/foo_folder'
    assert pc.get_path('..') == '/foo_folder'
    assert pc.get_path('/foo/bar/baz.txt') == '/foo_folder/foo/bar/baz.txt'


def test_get_globus_http_url(mock_projects):
    pc = PilotClient()
    pc.project.current = 'foo-project'
    url = pc.get_globus_http_url('foo.txt')
    purl = urlparse(url)
    foo = MOCK_PROJECTS['foo-project']
    assert purl.netloc == foo['endpoint'] + '.e.globus.org'
    assert purl.scheme == 'https'
    assert purl.path == '/foo_folder/foo.txt'


def test_get_globus_url(mock_projects):
    foo = MOCK_PROJECTS['foo-project']
    pc = PilotClient()
    pc.project.current = 'foo-project'
    url = pc.get_globus_url('metadata/foo.txt')
    purl = urlparse(url)
    assert purl.netloc == foo['endpoint']
    assert purl.scheme == 'globus'
    assert purl.path == '/foo_folder/metadata/foo.txt'


def test_get_globus_app_url(mock_projects):
    pc = PilotClient()
    pc.project.current = 'foo-project'
    url = pc.get_globus_app_url('metadata/foo.txt')
    purl = urlparse(url)
    assert purl.netloc == 'app.globus.org'
    assert purl.scheme == 'https'
    assert purl.path == '/file-manager'
    assert purl.query == 'origin_id=foo-project-endpoint&' \
                         'origin_path=%2Ffoo_folder%2Fmetadata%2Ffoo.txt'


def test_get_subject_url(mock_projects):
    pc = PilotClient()
    pc.project.current = 'foo-project'
    args = ('myfolder/dataframe.dat',)
    assert pc.get_globus_url(*args) == pc.get_subject_url(*args)

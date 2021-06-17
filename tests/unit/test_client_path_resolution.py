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


def test_build_short_path(mock_projects):
    pc = PilotClient()
    pc.project.current = 'foo-project'
    assert pc.build_short_path('foo', '/') == 'foo'
    assert pc.build_short_path('/foo/', '/') == 'foo'

    assert pc.build_short_path('foo', 'bar') == 'bar/foo'
    assert pc.build_short_path('/foo/', '/bar/') == 'bar/foo'


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


def test_get_portal_url(mock_projects, mock_context):
    pc = PilotClient()
    pc.project.current = 'foo-project'
    assert pc.get_portal_url('') == 'https://myportal/foo-project/'
    assert pc.get_portal_url('foo') == (
        'https://myportal/foo-project/'
        'globus%253A%252F%252Ffoo-project-endpoint%252Ffoo_folder%252Ffoo/'
    )
    cfg = mock_context.load()
    del cfg['contexts']['test-context']['projects_portal_url']
    mock_context.save(cfg)
    assert pc.get_portal_url('foo') is None


def test_get_short_path_valid_urls(mock_cli, mock_paths):
    short_path = mock_paths['short_path']
    for path in mock_paths.values():
        assert mock_cli.get_short_path(path) == short_path

    # This WORKS, even though its the wrong project, since we can't
    # resolve the base path for the project
    bar_path = mock_cli.get_path(short_path, project='bar-project')
    assert bar_path.endswith(short_path)


def test_get_short_path_invalid_urls(mock_cli):
    short_path = 'test_path'
    invalid = [
        f'ftp://{mock_cli.get_endpoint(project="bar-project")}/{short_path}',
        mock_cli.get_subject_url(short_path, project='bar-project'),
        mock_cli.get_globus_http_url(short_path, project='bar-project'),
    ]
    for i in invalid:
        with pytest.raises(PilotInvalidProject):
            mock_cli.get_short_path(i)


def test_resolve_project(mock_cli, mock_paths):
    paths = mock_paths['short_path'], mock_paths['full_path']
    urls = mock_paths['subject'], mock_paths['http']
    for path in paths:
        assert mock_cli.resolve_project(path) is None
    for url in urls:
        assert mock_cli.resolve_project(url) == mock_cli.get_project()


def test_resolve_context(mock_cli, mock_paths):
    paths = mock_paths['short_path'], mock_paths['full_path']
    urls = mock_paths['subject'], mock_paths['http']
    for path in paths:
        assert mock_cli.resolve_context(path) is None
    for url in urls:
        assert mock_cli.resolve_context(url) == mock_cli.get_context()

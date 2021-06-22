import pytest
import pilot.exc

from tests.unit.mocks import MULTI_FILE_DIR


def test_gather_metadata(mock_cli):
    # Should not raise errors

    metadata = mock_cli.gather_metadata(MULTI_FILE_DIR, '/')
    assert set(metadata) == {'files', 'dc', 'project_metadata'}
    assert len(metadata['files']) == 4
    expected_paths = [
        'multi_file/text_metadata.txt',
        'multi_file/folder/tsv1.tsv',
        'multi_file/folder/tinyimage.png',
        'multi_file/folder/folder2/tsv2.tsv',
    ]
    expected_urls = [mock_cli.get_globus_http_url(u) for u in expected_paths]
    urls = [f['url'] for f in metadata['files']]
    for url in urls:
        assert url in expected_urls


def test_gather_metadata_file_does_not_exist(mock_cli):
    with pytest.raises(pilot.exc.FileOrFolderDoesNotExist):
        mock_cli.gather_metadata('foo/', '/')


def test_gather_metadata_with_trailing_slash(mock_cli):
    # Should not raise errors
    trailing_slash_dataset = MULTI_FILE_DIR.rstrip('/') + '/'

    metadata = mock_cli.gather_metadata(trailing_slash_dataset, '/')
    assert set(metadata) == {'files', 'dc', 'project_metadata'}
    assert len(metadata['files']) == 4
    expected_paths = [
        'multi_file/text_metadata.txt',
        'multi_file/folder/tsv1.tsv',
        'multi_file/folder/tinyimage.png',
        'multi_file/folder/folder2/tsv2.tsv',
    ]
    expected_urls = [mock_cli.get_globus_http_url(u) for u in expected_paths]
    urls = [f['url'] for f in metadata['files']]
    for url in urls:
        assert url in expected_urls

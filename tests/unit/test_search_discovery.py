import os
from pilot.search_discovery import get_sub_in_collection, is_top_level
from tests.unit.mocks import CLIENT_FILE_BASE_DIR

MULTI_FILE_METADATA = os.path.join(CLIENT_FILE_BASE_DIR,
                                   'multi_file_entry.json')


def test_get_sub_in_collection(mock_multi_file_result):
    gmeta = mock_multi_file_result['gmeta']
    content = gmeta[0]
    mf_sub = gmeta[0]['subject']
    mf_tsv = os.path.join(mf_sub, 'folder/folder2/tsv2.tsv')
    no_exist = os.path.join(mf_sub, 'does_not_exist.csv')

    assert get_sub_in_collection(mf_sub, gmeta, precise=True) == content
    assert get_sub_in_collection(mf_tsv, gmeta, precise=True) == content
    assert get_sub_in_collection(no_exist, gmeta, precise=True) is None
    assert get_sub_in_collection(mf_tsv, gmeta, precise=False) == content


def test_get_sub_in_collection_none_on_non_single(mock_multi_file_result,
                                                  mock_cli):
    gmeta = mock_multi_file_result['gmeta']
    content1, sub1 = gmeta[0], gmeta[0]['subject']
    sub2 = mock_cli.get_subject_url('another_sub')
    url2 = mock_cli.get_globus_http_url('another_sub')
    ent2 = {'content': [{'files': [{'url': url2}]}], 'subject':  sub2}
    content2 = ent2

    gmeta.append(ent2)

    assert get_sub_in_collection(sub1, gmeta, precise=True) == content1
    assert get_sub_in_collection(sub2, gmeta, precise=True) == content2


def test_get_sub_in_collection_similar_subs(mock_multi_file_result, mock_cli):
    """
    Test for regression where similar subjects would match one another. For
    example:
    globus://foo-project-endpoint/foo_folder/foo
    globus://foo-project-endpoint/foo_folder/foofoo

    Searching for 'globus://foo-project-endpoint/foo_folder/foo' would match
    both above, resulting in the subject not being returned at all.
    """
    subs = ['foo', 'foofoo', 'bar']
    entries = [
        {
            'subject': mock_cli.get_subject_url(s),
            'content': [{'files': [{'url': mock_cli.get_globus_http_url(s)}]}]
        } for s in subs
    ]
    foofoo = mock_cli.get_subject_url('foofoo')
    foo = mock_cli.get_subject_url('foo')
    assert get_sub_in_collection(foofoo, entries, precise=True) is not None
    assert get_sub_in_collection(foofoo, entries, precise=False) is not None
    assert get_sub_in_collection(foo, entries, precise=True) is not None
    assert get_sub_in_collection(foo, entries, precise=False) is not None


def test_get_sub_in_collection_similar_file(mock_cli):
    files = ['foofoo']
    entries = [
        {
            'subject': mock_cli.get_subject_url('ent'),
            'content': [
                {'files': [
                    {'url': mock_cli.get_globus_http_url(f)} for f in files
                ]
                }
            ]
        }
    ]
    foo = mock_cli.get_subject_url('ent/foo')
    # File does not exist, but still produces match
    assert get_sub_in_collection(foo, entries, precise=False) is not None
    # Precise match required, returns None
    assert get_sub_in_collection(foo, entries, precise=True) is None


def test_get_sub_with_dirs(mock_multi_file_result, mock_cli):
    gmeta = mock_multi_file_result['gmeta']
    gmeta[0]['subject'] = mock_cli.get_subject_url('dir/file1.txt')
    sub2 = mock_cli.get_subject_url('dir/file2.txt')
    assert get_sub_in_collection(sub2, gmeta, precise=False) is None


def test_is_top_level(mock_multi_file_result):
    entry = mock_multi_file_result['gmeta'][0]['content'][0]
    assert is_top_level(entry, '/foo_folder/multi_file/') is True
    assert is_top_level(entry, '/foo_folder/multi_file') is True
    assert is_top_level(entry,
                        '/foo_folder/multi_file/text_metadata.txt') is False
    assert is_top_level(entry, '/foo_folder/multi_file/folder/') is False
    assert is_top_level(entry,
                        '/foo_folder/multi_file/folder/folder2') is False
    assert is_top_level(entry, '/foo_folder/multi_file/does_not_exst') is False

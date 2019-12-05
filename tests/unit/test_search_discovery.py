import os
from pilot.search_discovery import get_sub_in_collection
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

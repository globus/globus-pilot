import os
import time
import uuid

BASE_FILE_DIR = os.path.join(os.path.dirname(__file__), 'files')
COMMANDS_FILE_BASE_DIR = os.path.join(BASE_FILE_DIR, 'commands')
CLIENT_FILE_BASE_DIR = os.path.join(BASE_FILE_DIR, 'client')
ANALYSIS_FILE_BASE_DIR = os.path.join(BASE_FILE_DIR, 'analysis')
MIXED_BASE = os.path.join(ANALYSIS_FILE_BASE_DIR, 'types')
SCHEMA_FILE_BASE_DIR = os.path.join(BASE_FILE_DIR, 'schemas')

MIXED_MIMETYPES = [
    ('csv', 'text/csv'),
    ('tsv', 'text/tab-separated-values'),
    ('hdf', 'application/x-hdf'),
    ('feather', 'application/x-feather'),
    ('parquet', 'application/x-parquet'),
]

ANALYSIS_MIXED_FILES = [(os.path.join(MIXED_BASE, 'mixed.{}'.format(ext)), mt)
                        for ext, mt in MIXED_MIMETYPES]

DEFAULT_EXPIRE = int(time.time()) + 60 * 60 * 48


MOCK_PROJECTS = {
    'foo-project': {
        'title': 'Foo',
        'description': 'This is the foo project',
        'endpoint': 'foo-project-endpoint',
        'resource_server': 'foo_https_server',
        'search_index': 'foo-search-index',
        'base_path': '/foo_folder',
        'group': 'foo-group'
    },
    'foo-project-test': {
        'title': 'Foo Test',
        'description': 'This is the foo project',
        'endpoint': 'foo-project-test-endpoint',
        'resource_server': 'foo_https_server',
        'search_index': 'foo-test-search-index',
        'base_path': '/foo_test_folder',
        'group': 'foo-group'
    },
    'bar-project': {
        'description': 'This is the NCI Pilot Project testing project',
        'title': 'NCI Pilot 1 TEST',
        'endpoint': 'bar-project-endpoint',
        'resource_server': 'petrel_https_server',
        'search_index': 'bar-search-index',
        'base_path': '/bar_test_folder',
        'group': 'bar-group'
    },
}


MOCK_TOKEN_SET = {
    'auth.globus.org': {
        'scope': 'openid profile',
        'access_token': '<token>',
        'refresh_token': None,
        'token_type': 'Bearer',
        'expires_at_seconds': DEFAULT_EXPIRE,
        'resource_server': 'auth.globus.org'
    },
    'search.api.globus.org': {
        'scope': 'urn:globus:auth:scope:search.api.globus.org:all',
        'access_token': '<token>',
        'refresh_token': None,
        'token_type': 'Bearer',
        'expires_at_seconds': DEFAULT_EXPIRE,
        'resource_server': 'search.api.globus.org'
    },
    'transfer.api.globus.org': {
        'scope': 'urn:globus:auth:scope:transfer.api.globus.org:all',
        'access_token': '<token>',
        'refresh_token': None,
        'token_type': 'Bearer',
        'expires_at_seconds': DEFAULT_EXPIRE,
        'resource_server': 'transfer.api.globus.org'
    },
    'petrel.http.server': {
        'scope': 'https://auth.globus.org/scopes/'
                 '56ceac29-e98a-440a-a594-b41e7a084b62/all',
        'access_token': '<token>',
        'refresh_token': None,
        'token_type': 'Bearer',
        'expires_at_seconds': DEFAULT_EXPIRE,
        'resource_server': 'petrel.http.server'
    },
    'foo_https_server': {
        'scope': 'https://auth.globus.org/scopes/'
                 '56ceac29-e98a-440a-a594-b41e7a084b62/all',
        'access_token': '<token>',
        'refresh_token': None,
        'token_type': 'Bearer',
        'expires_at_seconds': DEFAULT_EXPIRE,
        'resource_server': 'foo_https_server'
    },

}

MOCK_PROFILE = {
    'name': 'Rosalind Franklin',
    'preferred_username': 'franklinr@globusid.org',
    'organization': 'The French Government Central Laboratory',
    'identity_provider': '41143743-f3c8-4d60-bbdb-eeecaba85bd9',
    'identity_provider_display_name': 'Globus ID',
    'sub': '102e192b-5acb-47ee-80c7-e613d86e7d6a',
}


class GlobusTransferTaskResponse(object):

    def __init__(self, *args, **kwargs):
        task_uuid = str(uuid.uuid4())
        self.data = {
            'DATA_TYPE': 'transfer_result',
            'code': 'Accepted',
            'message': 'The transfer has been accepted and a task has been '
                       'created and queued for execution',
            'request_id': 'foobarbaz',
            'resource': '/transfer',
            'submission_id': task_uuid,
            'task_id': task_uuid,
            'task_link': {
                'DATA_TYPE': 'link',
                'href': 'task/{}?format=json'.format(task_uuid),
                'rel': 'related',
                'resource': 'task',
                'title': 'related task'
            }
        }

    def __getitem__(self, item):
        return self.data[item]


class MemoryStorage(object):
    def __init__(self):
        super(MemoryStorage, self).__init__()
        self.tokens = {}
        self.data = {}

    def load(self):
        return self.data

    def save(self, data):
        self.data = data

    def write_tokens(self, tokens):
        self.tokens = tokens

    def read_tokens(self):
        return self.tokens

    def clear_tokens(self):
        self.tokens = {}

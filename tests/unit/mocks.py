import os
import time

TEST_FILE_BASE_DIR = os.path.join(os.path.dirname(__file__),
                                  'files', 'commands')
DEFAULT_EXPIRE = int(time.time()) + 60 * 60 * 48


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
    }
}


class MemoryStorage(object):
    def __init__(self):
        super(MemoryStorage, self).__init__()
        self.tokens = {}

    def write_tokens(self, tokens):
        self.tokens = tokens

    def read_tokens(self):
        return self.tokens

    def clear_tokens(self):
        self.tokens = {}
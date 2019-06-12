import os
import time
import requests
import globus_sdk
import urllib
from globus_sdk import AuthClient, SearchClient, TransferClient
from fair_research_login import NativeClient, LoadError
from pilot import project, profile, config, globus_clients


class PilotClient(NativeClient):

    DEFAULT_SCOPES = [
        'profile',
        'openid',
        'urn:globus:auth:scope:search.api.globus.org:all',
        'urn:globus:auth:scope:transfer.api.globus.org:all',
        'https://auth.globus.org/scopes/'
        '56ceac29-e98a-440a-a594-b41e7a084b62/all',
    ]
    CLIENT_ID = 'e4d82438-00df-4dbd-ab90-b6258933c335'
    APP_NAME = 'NCI Pilot 1 Dataframe Manager'

    def __init__(self):
        self.config = config.Config()
        super().__init__(client_id=self.CLIENT_ID,
                         token_storage=self.config,
                         default_scopes=self.DEFAULT_SCOPES,
                         app_name=self.APP_NAME)
        self.project = project.Project(self)
        self.profile = profile.Profile()

    def login(self, *args, **kwargs):
        super().login(*args, **kwargs)

        ac_authorizer = self.get_authorizers()['auth.globus.org']
        auth_cli = AuthClient(authorizer=ac_authorizer)
        user_info = auth_cli.oauth2_userinfo()
        self.profile.save_user_info(user_info.data)

    def logout(self):
        super().logout()
        self.config.clear()

    def is_logged_in(self):
        try:
            self.load_tokens()
            return True
        except LoadError:
            return False

    @property
    def gsearch(self):
        authorizer = self.get_authorizers()['search.api.globus.org']
        return SearchClient(authorizer=authorizer)

    @property
    def gtransfer(self):
        authorizer = self.get_authorizers()['transfer.api.globus.org']
        return TransferClient(authorizer=authorizer)

    def get_http_client(self, project=None):
        base_url = self.get_globus_http_url(
            '', project=project, relative=False)
        rs = self.project.get_info(project)['resource_server']
        auth = self.get_authorizers()[rs]
        return globus_clients.HTTPSClient(authorizer=auth, base_url=base_url)

    def ls(self, path, project=None, relative=True):
        path = self.get_path(path, project, relative)
        endpoint = self.get_endpoint(project)
        r = self.gtransfer.operation_ls(endpoint, path=path)
        return [f['name'] for f in r['DATA'] if f['type'] == 'dir']

    def get_group(self, project=None):
        return self.project.get_info(project)['group']

    def get_endpoint(self, project=None):
        return self.project.get_info(project)['endpoint']

    def get_index(self, project=None):
        return self.project.get_info(project)['search_index']

    def get_path(self, path, project=None, relative=True):
        bdir = self.project.get_info(project)['base_path'] if relative else ''
        return os.path.join(bdir, path)

    def get_globus_http_url(self, path, project=None, relative=True):
        host = '{}.e.globus.org'.format(self.get_endpoint(project))
        path = self.get_path(path, project, relative)
        parts = ['https', host, path, '', '', '']
        return urllib.parse.urlunparse(parts)

    def get_globus_url(self, path, project=None, relative=True):
        path = self.get_path(path, project, relative)
        parts = ['globus', self.get_endpoint(project), path, '', '', '']
        return urllib.parse.urlunparse(parts)

    def get_globus_app_url(self, path, project=None, relative=True):
        path = self.get_path(path, project, relative)
        params = {'origin_id': self.get_endpoint(project), 'origin_path': path}
        return urllib.parse.urlunparse([
            'https', 'app.globus.org', 'file-manager', '',
            urllib.parse.urlencode(params), ''
        ])

    def get_subject_url(self, path, project=None, relative=True):
        return self.get_globus_url(path, project, relative)

    def get_search_entry(self, path, project=None, relative=True):
        subject = self.get_subject_url(path, project, relative)
        try:
            entry = self.gsearch.get_subject(self.get_index(project), subject)
            return entry['content'][0]
        except globus_sdk.exc.SearchAPIError:
            return None

    def ingest_entry(self, gmeta_entry, test=False):
        """
        Ingest a complete gmeta_entry into search. If test is true, the test
        search index will be used instead.
        Waits on tasks until they succeed or fail:
            https://docs.globus.org/api/search/task/
        :param gmeta_entry:
        :param test: Use the test index instead?
        :return: True on success Raises exception on fail
        """
        sc = self.gsearch
        result = sc.ingest(self.get_index(test), gmeta_entry)
        pending_states = ['PENDING', 'PROGRESS']
        while sc.get_task(result['task_id'])['state'] in pending_states:
            time.sleep(.2)
        if sc.get_task(result['task_id'])['state'] != 'SUCCESS':
            raise Exception('Failed to ingest search subject')
        return True

    def delete_entry(self, path, entry_id=None, full_subject=False):
        """
        Delete search entries in Globus Search. dataframe and directory
        reference the real path of the dataframe on a globus endpoint, and
        generates the subject id used to delete the entry on globus search.
        Test denotes whether to use the test or production search index.
        entry_id will delete only a subset of the subject, where full_subject
        will delete the entire subject. full_subject overrides entry_id.

        Example: delete_entry('foo', 'bar', True, entry_id='foo/bar')
                 delete_entry('baz', 'car', False)
        :param dataframe: filename reference to fetch the subject
        :param directory: directory reference to fetch the subject
        :param test: Delete on the test index
        :param entry_id: Single entry within the subject to delete.
        :param full_subject: Delete the whole subject and all its entries
        :return:
        """
        index, subject = self.get_index(), self.get_subject_url(path)
        if full_subject:
            return self.gsearch.delete_subject(index, subject)
        else:
            return self.gsearch.delete_entry(index, subject, entry_id=entry_id)

    def upload(self, dataframe, destination, test=False):
        filename = os.path.basename(dataframe)
        url = self.get_globus_http_url(filename, destination, test)

        with open(dataframe, 'rb') as fh:
            # Get the user info as JSON
            resp = requests.put(
                url, headers=self.http_headers, data=fh, allow_redirects=False)
            return resp

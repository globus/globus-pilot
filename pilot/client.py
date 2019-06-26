import os
import time
import globus_sdk
import urllib
import logging
from globus_sdk import AuthClient, SearchClient, TransferClient
from fair_research_login import NativeClient, LoadError
from pilot import project, profile, config, globus_clients, exc, logging_cfg

logging_cfg.setup_logging()
log = logging.getLogger(__name__)


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
        auth_cli = self.get_auth_client()
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

    def get_auth_client(self):
        authorizer = self.get_authorizers()['auth.globus.org']
        return AuthClient(authorizer=authorizer)

    def get_search_client(self):
        authorizer = self.get_authorizers()['search.api.globus.org']
        return SearchClient(authorizer=authorizer)

    def get_transfer_client(self):
        authorizer = self.get_authorizers()['transfer.api.globus.org']
        return TransferClient(authorizer=authorizer)

    def get_http_client(self, project):
        # Fetch the base url for the globus http endpoint
        url = urllib.parse.urlparse(self.get_globus_http_url(''))
        base_url = urllib.parse.urlunparse((url.scheme, url.netloc, '', '',
                                            '', ''))
        rs = self.project.get_info(project)['resource_server']
        auth = self.get_authorizers()[rs]
        return globus_clients.HTTPFileClient(authorizer=auth,
                                             base_url=base_url)

    def get_group(self, project=None):
        return self.project.get_info(project)['group']

    def get_endpoint(self, project=None):
        return self.project.get_info(project)['endpoint']

    def get_index(self, project=None):
        return self.project.get_info(project)['search_index']

    def get_path(self, path, project=None, relative=True):
        """
        Resolve the absolute Globus endpoint path given a relative project
        path. Raises PilotClientException if relative=False and path is not
        in the project's directory.
        :param path: Path to file or directory
        :param project: The project to use. Defaults to current project
        :param relative: If True, prepends the path to the project. If False,
        does not prepend path but ensures it's in the project's directory
        :return:
        """
        bdir = self.project.get_info(project)['base_path']
        path = path.lstrip('.')
        if relative is True:
            path = path.lstrip('/')
            if path:
                path = os.path.join(bdir, path.lstrip('/'))
            else:
                path = bdir
        else:
            if bdir not in path:
                raise exc.PilotClientException(
                    'Absolute path {} not in project {} path {}'.format(
                        path, project or self.project.current, bdir)
                )
        log.debug('Path: {}'.format(path))
        return path

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

    def ls(self, path, project=None, relative=True):
        path = self.get_path(path, project, relative)
        endpoint = self.get_endpoint(project)
        r = self.get_transfer_client().operation_ls(endpoint, path=path)
        return [f['name'] for f in r['DATA']]

    def mkdir(self, path, project=None, relative=True):
        rpath = self.get_path(path, project=project, relative=relative)
        tc = self.get_transfer_client()
        tc.operation_mkdir(self.get_endpoint(project), rpath)

    def get_search_entry(self, path, project=None, relative=True):
        sc = self.get_search_client()
        subject = self.get_subject_url(path, project, relative)
        try:
            entry = sc.get_subject(self.get_index(project), subject)
            return entry['content'][0]
        except globus_sdk.exc.SearchAPIError:
            return None

    def ingest_entry(self, gmeta_entry):
        """
        Ingest a complete gmeta_entry into search. If test is true, the test
        search index will be used instead.
        Waits on tasks until they succeed or fail:
            https://docs.globus.org/api/search/task/
        :param gmeta_entry:
        :param test: Use the test index instead?
        :return: True on success Raises exception on fail
        """
        sc = self.get_search_client()
        result = sc.ingest(self.get_index(), gmeta_entry)
        pending_states = ['PENDING', 'PROGRESS']
        log.debug(f'Ingesting to {self.get_index()}')
        task_status = sc.get_task(result['task_id'])['state']
        while task_status in pending_states:
            log.debug(f'Search task still {task_status}')
            time.sleep(.2)
            task_status = sc.get_task(result['task_id'])['state']
        if sc.get_task(result['task_id'])['state'] != 'SUCCESS':
            raise exc.PilotClientException('Failed to ingest search subject')
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
        search_cli = self.get_search_client()
        if full_subject:
            return search_cli.delete_subject(index, subject)
        else:
            return search_cli.delete_entry(index, subject, entry_id=entry_id)

    def upload(self, dataframe, destination, project=None):
        path = self.get_path(destination, project=project)
        return self.get_http_client(project).put(path, filename=dataframe)

    def download(self, path, project=None, relative=True, range=None,
                 yield_written=False):
        fname = os.path.basename(path)
        url = self.get_path(path, project=project, relative=relative)
        http_client = self.get_http_client(project=project)
        log.debug(f'Fetching item {url}')
        response = http_client.get(url, range=range)
        with open(fname, 'wb') as fh:
            for part in response.iter_content:
                bytes_written = fh.write(part)
                if yield_written:
                    yield bytes_written
        log.debug('Fetch Successful')

    def delete(self, path, project=None, relative=True, recursive=False):
        tc = self.get_transfer_client()
        endpoint = self.get_endpoint(project)
        full_path = self.get_path(path, project=project, relative=relative)
        log.debug(f'Deleting item '
                  f'{self.project.lookup_endpoint(endpoint)}{full_path}')
        ddata = globus_sdk.DeleteData(
            tc, endpoint, recursive=recursive, notify_on_succeeded=False,
            label=f'File Deletion with {self.app_name}')
        ddata.add_item(full_path)
        delete_result = tc.submit_delete(ddata)
        tc.task_wait(delete_result.data['task_id'])
        log.debug('Success!')

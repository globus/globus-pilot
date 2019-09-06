import os
import time
import globus_sdk
import urllib
import logging
from globus_sdk import AuthClient, SearchClient, TransferClient
from fair_research_login import NativeClient, LoadError, ScopesMismatch
from pilot import (
    project, profile, config, globus_clients, exc, logging_cfg, context
)

logging_cfg.setup_logging()
log = logging.getLogger(__name__)


class PilotClient(NativeClient):
    r"""
    The Pilot Client is the core class of this library, providing a set of
    operations to authenticate users, track which project they're using, and
    handle core operations such as login, logout, upload, download,
    building URLs, and getting authenticated Globus Service clients.

    ** Methods **

    *  :py:meth:`.login`
    *  :py:meth:`.logout`
    *  :py:meth:`.is_logged_in`
    *  :py:meth:`.get_auth_client`
    *  :py:meth:`.get_search_client`
    *  :py:meth:`.get_transfer_client`
    *  :py:meth:`.get_http_client`
    *  :py:meth:`.get_group`
    *  :py:meth:`.get_endpoint`
    *  :py:meth:`.get_index`
    *  :py:meth:`.get_path`
    *  :py:meth:`.get_globus_http_url`
    *  :py:meth:`.get_globus_url`
    *  :py:meth:`.get_globus_app_url`
    *  :py:meth:`.get_portal_url`
    *  :py:meth:`.get_globus_app_url`
    *  :py:meth:`.get_subject_url`
    *  :py:meth:`.ls`
    *  :py:meth:`.mkdir`
    *  :py:meth:`.get_search_entry`
    *  :py:meth:`.ingest_entry`
    *  :py:meth:`.delete_entry`
    *  :py:meth:`.upload`
    *  :py:meth:`.download`
    *  :py:meth:`.delete`
    ** Example **
    Login, upload, show various access methods, then delete.

    from pilot.search import scrape_metadata, gen_gmeta
    pc = PilotClient()
    pc.login()
    pc.project.current = 'foo'
    pc.mkdir('bar')
    pc.ls('bar')

    metadata = scrape_metadata('moo.txt')
    gmeta = gen_gmeta(pc.get_subject_url('bar/moo.txt'), ['public'], metadata)
    pc.ingest_entry(gmeta)
    pc.upload('moo.txt', 'bar')

    pc.get_path('bar/moo.txt')
    pc.get_portal_url('bar/moo.txt')
    pc.get_globus_app_url('bar/moo.txt')
    pc.get_globus_http_url('bar/moo.txt')
    pc.download('bar/moo.txt')

    pc.delete_entry('bar/moo.txt')
    pc.delete('bar/moo.txt')

    """
    DEFAULT_SCOPES = [
        'profile',
        'openid',
        'urn:globus:auth:scope:search.api.globus.org:all',
        'urn:globus:auth:scope:transfer.api.globus.org:all',
    ]
    GROUPS_SCOPE = 'urn:globus:auth:scope:nexus.api.globus.org:groups'

    def __init__(self):
        self.config = config.Config()
        self.context = context.Context(self)
        default_scopes = self.context.get_value('scopes')
        default_scopes = default_scopes or self.DEFAULT_SCOPES

        super().__init__(client_id=self.context.get_value('client_id'),
                         token_storage=self.config,
                         default_scopes=default_scopes,
                         app_name=self.context.get_value('app_name'))
        self.project = project.Project()
        self.profile = profile.Profile()

    def login(self, *args, **kwargs):
        r"""
        Do a Native App Auth Flow to get tokens for requested scopes, for
        general project usage
        **Parameters**
        ``no_local_server`` (*bool*)
          Disable spinning up a local server to automatically copy-paste the
          auth code. THIS IS REQUIRED if you are on a remote server, as this
          package isn't able to determine the domain of a remote service. When
          used locally with no_local_server=False, the domain is localhost with
          a randomly chosen open port number.
        ``no_browser`` (*string*)
          Do not automatically open the browser for the Globus Auth URL.
          Display the URL instead and let the user navigate to that location.
        ``requested_scopes`` (*list*)
          A list of scopes to request of Globus Auth during login.
          Example:
          ['openid', 'profile', 'email']
        ``refresh_tokens`` (*bool*)
          Ask for Globus Refresh Tokens to extend login time.
        ``force`` (*bool*)
          Force a login flow, even if loaded tokens are valid.
        """
        super().login(*args, **kwargs)
        auth_cli = self.get_auth_client()
        user_info = auth_cli.oauth2_userinfo()
        self.profile.save_user_info(user_info.data)

    def logout(self):
        """Clear tokens from configfile"""
        super().logout()
        self.config.clear()

    def is_logged_in(self):
        """Check if the user is logged in and tokens are active."""
        try:
            self.load_tokens(requested_scopes=self.context.get_value('scopes'))
            return True
        except LoadError:
            return False

    def get_auth_client(self):
        """
        Returns a live Globus Auth Client based on user login info.
        https://globus-sdk-python.readthedocs.io/en/stable/clients/auth/
        :return:
        """
        authorizer = self.get_authorizers()['auth.globus.org']
        return AuthClient(authorizer=authorizer)

    def get_search_client(self):
        """Returns a live Search Client based on user login info
        https://globus-sdk-python.readthedocs.io/en/stable/clients/search/
        """
        authorizer = self.get_authorizers()['search.api.globus.org']
        return SearchClient(authorizer=authorizer)

    def get_transfer_client(self):
        """
        Returns a live transfer client based on user info
        https://globus-sdk-python.readthedocs.io/en/stable/clients/transfer/
        """
        authorizer = self.get_authorizers()['transfer.api.globus.org']
        return TransferClient(authorizer=authorizer)

    def get_nexus_client(self):
        """
        Returns a nexus client, used for groups. Please don't use this directly
        """
        rs = {'requested_scopes': [self.GROUPS_SCOPE]}
        try:
            authorizer = self.get_authorizers_by_scope(**rs)[self.GROUPS_SCOPE]
            return globus_clients.NexusClient(authorizer=authorizer)
        except ScopesMismatch:
            return None

    def get_http_client(self, project):
        r"""
        Returns a general Globus HTTP Client for http uploads/downloads
        **Parameters**
        ``project`` (*bool*)
          The project to upload/download to/from
        """
        # Fetch the base url for the globus http endpoint
        url = urllib.parse.urlparse(self.get_globus_http_url(''))
        base_url = urllib.parse.urlunparse((url.scheme, url.netloc, '', '',
                                            '', ''))
        rs = self.project.get_info(project)['resource_server']
        auth = self.get_authorizers()[rs]
        return globus_clients.HTTPFileClient(authorizer=auth,
                                             base_url=base_url)

    def get_group(self, project=None):
        """
        Get the group for a given project.
        **Parameters**
        ``project`` (*string*)
          The project to fetch info for. Defaults to current project
        """
        return self.project.get_info(project)['group'] or 'public'

    def get_endpoint(self, project=None):
        """
        Get the configured Globus Endpoint for the given project. Project
        defaults to current project if None.
        **Parameters**
        ``project`` (*string*)
          The project to fetch info for. Defaults to current project
        """
        return self.project.get_info(project)['endpoint']

    def get_index(self, project=None):
        """
        Get the configured search index for the given project. Project defaults
        to current project if None.
        **Parameters**
        ``project`` (*string*)
          The project to fetch info for. Defaults to current project
        """
        return self.project.get_info(project)['search_index']

    def get_path(self, path, project=None, relative=True):
        """
        Resolve the absolute Globus endpoint path given a relative project
        path. Raises PilotClientException if relative=False and path is not
        in the project's directory.
        **Parameters**
        ``path`` (*path string*)
          Path to a local resource on this project
        ``project`` (*string*)
          The project to fetch info for. Defaults to current project
        ``relative`` (*bool*)
          If True, prepends the path to the project. If False,
          does not prepend path but ensures it's in the project's directory
        **Examples**
        >>> pc.get_path('foo/bar.txt')
        '/projects/myproject/foo/bar.txt'
        >>> pc.get_path('/projects/goo/moo.txt', project='goo', relative=False)
        '/projects/goo/moo.txt'
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
                log.warning(
                    'Absolute path {} not in project {} path {}'.format(
                        path, project or self.project.current, bdir)
                )
        log.debug('Path: {}'.format(path))
        return path

    def get_globus_http_url(self, path, project=None, relative=True):
        """
        Resolve an http url based on the path.
        **Parameters**
        ``path`` (*path string*)
          Path to a local resource on this project
        ``project`` (*string*)
          The project to fetch info for. Defaults to current project
        ``relative`` (*bool*)
          If True, prepends the path to the project. If False,
          does not prepend path but ensures it's in the project's directory
        **Examples**
        >>> pc.get_globus_http_url('foo/bar.txt')
        'https://5590f6aa-a9f7-4cc3-b130-afc26e2ca0c0.e.globus.org/projects/
         myproject/foo/bar.txt'
        """
        host = '{}.e.globus.org'.format(self.get_endpoint(project))
        path = self.get_path(path, project, relative)
        parts = ['https', host, path, '', '', '']
        return urllib.parse.urlunparse(parts)

    def get_globus_url(self, path, project=None, relative=True):
        """
        Resolve a Globus URL for a resource on a Globus Endpoint
        **Parameters**
        ``path`` (*path string*)
          Path to a local resource on this project
        ``project`` (*string*)
          The project to fetch info for. Defaults to current project
        ``relative`` (*bool*)
          If True, prepends the path to the project. If False,
          does not prepend path but ensures it's in the project's directory
        **Examples**
        >>> pc.get_globus_url('foo/bar.txt')
        'globus://5590f6aa-a9f7-4cc3-b130-afc26e2ca0c0/projects/myproject/
         foo/bar.txt'
        """
        path = self.get_path(path, project, relative)
        parts = ['globus', self.get_endpoint(project), path, '', '', '']
        return urllib.parse.urlunparse(parts)

    def get_globus_app_url(self, path, project=None, relative=True):
        """
        Resolve a URL to the Globus Webapp
        **Parameters**
        ``path`` (*path string*)
          Path to a local resource on this project
        ``project`` (*string*)
          The project to fetch info for. Defaults to current project
        ``relative`` (*bool*)
          If True, prepends the path to the project. If False,
          does not prepend path but ensures it's in the project's directory
        **Examples**
        >>> pc.get_globus_app_url('foo/bar.txt')
        'https://app.globus.org/file-manager?
         origin_id=e55b4eab-6d04-11e5-ba46-22000b92c6ec&
         origin_path=%2FXPCSDATA%2Ftest%2Fnick-testing%2Ffoo%2Fbar.txt'
        """
        path = self.get_path(path, project, relative)
        params = {'origin_id': self.get_endpoint(project), 'origin_path': path}
        return urllib.parse.urlunparse([
            'https', 'app.globus.org', 'file-manager', '',
            urllib.parse.urlencode(params), ''
        ])

    def get_portal_url(self, path=None, project=None):
        """
        Resolve a URL to the Globus Webapp
        **Parameters**
        ``path`` (*path string*)
          Path to a local resource on this project
        ``project`` (*string*)
          The project to fetch info for. Defaults to current project
        **Examples**
        >>> pc.get_portal_url('foo/bar.txt')
        'https://myportal/foo/bar.txt'
        """
        portal_url = self.context.get_value('projects_portal_url')
        if not portal_url:
            return None
        project = project or self.project.current
        subject = ''
        if path:
            sub = self.get_subject_url(path, project=project)
            subject = urllib.parse.quote_plus(urllib.parse.quote_plus(sub))
        portal_url = portal_url.format(project=project, subject=subject)
        # If no subject was given, remove trailing slash
        if portal_url.endswith('//'):
            portal_url = portal_url[0:-1]
        return portal_url

    def get_subject_url(self, path, project=None, relative=True):
        """
        Resolve a subject URL for a given resource, as it should appear as a
        subject in Globus Search. Typically this is the same as a "Globus" URL
        and is equivalent to get_globus_url()
        """
        return self.get_globus_url(path, project, relative)

    def ls(self, path, project=None, relative=True, extended=False):
        """
        Perform a list on the remote endpoint for the given project, and list
        the contents of 'path'. Returns contents in a list.
        **Parameters**
        ``path`` (*path string*)
          Path to a local resource on this project
        ``project`` (*string*)
          The project to fetch info for. Defaults to current project
        ``relative`` (*bool*)
          If True, prepends the path to the project. If False,
          does not prepend path but ensures it's in the project's directory
        ``extended`` (*bool*)
          Return a dict instead for each value, where the key is each item of
          content and the values are all file details for each item.
        **Examples**
        >>> pc.ls('bar')
        ['file1.png', 'foo', 'moo']
        """
        path = self.get_path(path, project, relative)
        endpoint = self.get_endpoint(project)
        r = self.get_transfer_client().operation_ls(endpoint, path=path)
        if extended:
            return {f['name']: f for f in r['DATA']}
        return [f['name'] for f in r['DATA']]

    def mkdir(self, path, project=None, relative=True):
        """
        Create a directory in the given project
        **Parameters**
        ``path`` (*path string*)
          Path to a local resource on this project
        ``project`` (*string*)
          The project to fetch info for. Defaults to current project
        ``relative`` (*bool*)
          If True, prepends the path to the project. If False,
          does not prepend path but ensures it's in the project's directory
        **Examples**
        >>> pc.mkdir('myfolder')
        """
        rpath = self.get_path(path, project=project, relative=relative)
        tc = self.get_transfer_client()
        tc.operation_mkdir(self.get_endpoint(project), rpath)

    def get_search_entry(self, path, project=None, relative=True):
        """
        Get a search entry for a given resource
        **Parameters**
        ``path`` (*path string*)
          Path to a local resource on this project
        ``project`` (*string*)
          The project to fetch info for. Defaults to current project
        ``relative`` (*bool*)
          If True, prepends the path to the project. If False,
          does not prepend path but ensures it's in the project's directory
        **Examples**
        >>> pc.get_search_entry('foo.txt')
          {'dc': {'creators': [{'creatorName': 'NOAA'}],
            'dates': [{'date': '2019-08-29T19:36:13.064917Z',
                    'dateType': 'Created'}],
             ...
          }
        """
        sc = self.get_search_client()
        subject = self.get_subject_url(path, project, relative)
        try:
            entry = sc.get_subject(self.get_index(project), subject)
            return entry['content'][0]
        except globus_sdk.exc.SearchAPIError:
            return None

    def ingest_entry(self, gmeta_entry, index=None):
        """
        Ingest a complete gmeta_entry into search.
        **Parameters**
        ``gmeta_entry`` (*dict*)
          A dict matching a Globus Search gmeta entry. An example is here:
          https://globus-sdk-python.readthedocs.io/en/stable/clients/search/#globus_sdk.SearchClient.ingest  # noqa
          {'@version': '2016-11-09',
           'ingest_data': {'@version': '2016-11-09',
                             'gmeta': [{'@version': '2016-11-09',
                                        'content': {},
                                        'id': 'metadata',
                                        'subject': 'foo',
                                        'visible_to': ['public']}]},
           'ingest_type': 'GMetaList'}
        ``index`` (*string*)
          The index to ingest to. Defaults to configured current project index
        **Examples**
        >>> from pilot.search import scrape_metadata, gen_gmeta
        >>> metadata = scrape_metadata('moo.txt')
        >>> subject = pc.get_subject_url('bar/moo.txt')
        >>> group = pc.get_group()
        >>> gmeta = gen_gmeta(subject, [group], metadata)
        >>> pc.ingest_entry(gmeta)
        True
        """
        sc = self.get_search_client()
        index = index or self.get_index()
        result = sc.ingest(index, gmeta_entry)
        pending_states = ['PENDING', 'PROGRESS']
        log.debug('Ingesting to {}'.format(index))
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
        Delete a search entry in Globus Search.
        **Parameters**
        ``path`` (*path string*)
          Path to a local resource on this project
        ``entry_id`` (*string*)
          Name of the entry to delete.
        ``full_subject`` (*bool*)
          Delete all entries in the subject. This is typically equivalent to
          normal deletes if only one entry exists for the given subject.
        **Examples**
        >>> pc.delete_entry('foo/bar.txt')
        >>> pc.delete_entry('moo.txt', entry_id='special_metadata')
        >>> pc.delete_entry('goo.json' full_subject=True)
        """
        index, subject = self.get_index(), self.get_subject_url(path)
        search_cli = self.get_search_client()
        if full_subject:
            return search_cli.delete_subject(index, subject)
        else:
            return search_cli.delete_entry(index, subject, entry_id=entry_id)

    def upload(self, dataframe, destination, project=None):
        """
        Upload a dataframe to a destination on a project
        **Parameters**
        ``dataframe`` (*path-to-file*)
          Path to a file on the local system
        ``destination`` (*path-string*)
          Path to upload on the remote endpoint
        ``project`` (*string*)
          The project to fetch info for. Defaults to current project
        **Examples**

        """
        short_path = os.path.join(destination, os.path.basename(dataframe))
        path = self.get_path(short_path, project=project)
        return self.get_http_client(project).put(path, filename=dataframe)

    def download_parts(self, path, project=None, relative=True, range=None):
        """Download a file in parts over HTTP and yield the number of bytes
        written for each part. Yields a generator for each part."""
        fname = os.path.basename(path)
        url = self.get_path(path, project=project, relative=relative)
        http_client = self.get_http_client(project=project)
        log.debug(f'Fetching item {url}')
        response = http_client.get(url, range=range)
        with open(fname, 'wb') as fh:
            for part in response.iter_content:
                yield fh.write(part)
        log.debug('Fetch Successful')
        return 0

    def download(self, path, project=None, relative=True, range=None):
        """
        Download a file to the local system using HTTPS to the local filesystem
        using the 'path' basename. Returns the total number of bytes written
        to the filesystem.
        **Parameters**
        ``path`` (*path string*)
          Path to a local resource on this project
        ``project`` (*string*)
          The project to fetch info for. Defaults to current project
        ``relative`` (*bool*)
          If True, prepends the path to the project. If False,
          does not prepend path but ensures it's in the project's directory
        ``range`` (*string*)
          Specify a byte range to fetch from the file. Range must be in the
          format: "0-10,15-20" where each number is a byte.
        **Examples**
        >>> pc.download('foo.txt')
        >>> pc.download('foo.txt', project='bar', range='0-100')
        >>> pc.download('bar/moo.txt', range='0-100,150-200')
        """
        parts = self.download_parts(path, project, relative, range)
        parts = [p for p in parts]
        print(parts)
        return sum(parts)
        return sum(self.download_parts(path, project, relative, range))

    def delete(self, path, project=None, relative=True, recursive=False):
        """
        Delete a file on the remote endpoint for the given project.
        to the filesystem.
        **Parameters**
        ``path`` (*path string*)
          Path to a local resource on this project
        ``project`` (*string*)
          The project to fetch info for. Defaults to current project
        ``relative`` (*bool*)
          If True, prepends the path to the project. If False,
          does not prepend path but ensures it's in the project's directory
        ``recursive`` (*bool*)
          If the 'path' refers to a folder, delete everything inside it
        **Examples**
        >>> pc.delete('foo.txt')
        >>> pc.delete('bar', recursive=True)
        """
        tc = self.get_transfer_client()
        endpoint = self.get_endpoint(project)
        full_path = self.get_path(path, project=project, relative=relative)
        app_name = self.context.get_value('app_name')
        ddata = globus_sdk.DeleteData(
            tc, endpoint, recursive=recursive, notify_on_succeeded=False,
            label='File Deletion with {}'.format(app_name))
        ddata.add_item(full_path)
        delete_result = tc.submit_delete(ddata)
        tc.task_wait(delete_result.data['task_id'])
        log.debug('Success!')

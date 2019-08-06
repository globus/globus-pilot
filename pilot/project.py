import logging
import time
from pilot import config
from pilot.exc import PilotInvalidProject
from pilot.search import gen_gmeta

log = logging.getLogger(__name__)


class Project(config.ConfigSection):

    SECTION = 'project'
    DEFAULT_PROJECT = 'ncipilot1'
    PROJECTS_MANIFEST = 'pilot1-tools-project-manifest-v2.json'
    PROJECTS_ENDPOINT = 'ebf55996-33bf-11e9-9fa4-0a06afd4a22e'
    PROJECTS_GROUP = '679d11e1-5c7d-11e9-8ab8-0e4a32f5e3b8'
    PROJECTS_PATH = '/projects'
    # Cache will go stale in a day
    CACHE_TIMEOUT_SECONDS = 60 * 60 * 24
    ENDPOINTS = {'petrel#ncipilot': 'ebf55996-33bf-11e9-9fa4-0a06afd4a22e'}
    PROJECTS_MANIFEST_INDEX = '889729e8-d101-417d-9817-fa9d964fdbc9'
    DEFAULT_SEARCH_INDEX = '889729e8-d101-417d-9817-fa9d964fdbc9'
    DEFAULT_RESOURCE_SERVER = 'petrel_https_server'

    def __init__(self, client):
        super().__init__()
        self.client = client

    def get_manifest_subject(self):
        return 'globus://{}'.format(self.PROJECTS_MANIFEST)

    def update(self, index=None, dry_run=False, update_groups_cache=True):
        """Update the local list of projects and groups."""
        self.reset_cache_timer()
        sub = self.get_manifest_subject()
        index = index or self.PROJECTS_MANIFEST_INDEX
        sc = self.client.get_search_client()
        manifest = sc.get_subject(index, sub).data['content'][0]
        if update_groups_cache is True:
            log.debug('Updating groups...')
            subgroups = self.fetch_subgroups(group=self.PROJECTS_GROUP)
            groups = {sg['name']: sg['id'] for sg in subgroups}
            if groups:
                manifest['groups'] = groups
            else:
                log.warning('No groups returned, user may not have access to '
                            'subgroups for this group.')
        if dry_run is False:
            cfg = self.config.load()
            cfg['projects'] = manifest['projects']
            cfg['groups'] = manifest['groups']
            cfg.write()
        return manifest

    def update_with_diff(self, index=None, dry_run=False,
                         update_groups_cache=True):
        new = self.update(index=index, dry_run=dry_run,
                           update_groups_cache=update_groups_cache)
        return {
            'projects': self.get_diff(self.load_all(), new['projects']),
            'groups': self.get_diff(self.load_groups(), new['groups'])
        }

    def get_diff(self, old, new):
        """Fetch the differences between two dictionaries"""
        oldk, newk = set(old.keys()), set(new.keys())
        diff = dict()
        diff['removed'] = {k: old[k] for k in oldk - newk}
        diff['added'] = {k: new[k] for k in newk - oldk}
        diff['changed'] = {}
        for k in oldk.intersection(newk):
            if old[k] != new[k]:
                changed = [pk for pk in set(old[k]).union(set(new[k]))
                           if old[k].get(pk) != new[k].get(pk)]
                changed_str = [f'{old[k][c]} --> {new[k][c]}'
                               for c in changed]
                diff['changed'][k] = dict(zip(changed, changed_str))
        return diff

    def reset_cache_timer(self):
        self.save_option('last_update', int(time.time()))

    def is_cache_stale(self):
        if not self.load_all():
            return True
        last_updated = self.load_option('last_update')
        if last_updated:
            if time.time() < int(last_updated) + self.CACHE_TIMEOUT_SECONDS:
                return False
        return True

    def push(self, index=None):
        sub = self.get_manifest_subject()
        index = index or self.PROJECTS_MANIFEST_INDEX
        manifest = {
            'projects': dict(self.load_all()),
            'groups': dict(self.load_groups()),
        }
        gmeta = gen_gmeta(sub, ['public'], manifest)
        self.client.ingest_entry(gmeta, index=index)

    def load_all(self):
        return self.config.load().get('projects', {})

    def load_groups(self):
        return dict(self.config.load().get('groups', {}))

    def fetch_subgroups(self, group=None):
        nc = self.client.get_nexus_client()
        resp = nc.get_subgroups(group or self.PROJECTS_GROUP)
        return resp.data.json().get('children')

    def get_info(self, project=None):
        if project is None:
            project = self.current
        pinfo = self.load_all().get(project)
        if pinfo is None:
            raise PilotInvalidProject(f'No project exists {project}')
        return pinfo

    def is_set(self):
        """Returns true if a project has been set, false otherwise"""
        try:
            return self.current and self.current in self.load_all().keys()
        except PilotInvalidProject:
            return False

    def set_project(self, slug, project_data):
        cfg = self.config.load()
        cfg['projects'][slug] = project_data
        cfg.write()

    def delete_project(self, slug):
        if self.current == slug:
            self.current = None
        cfg = self.config.load()
        del cfg['projects'][slug]
        cfg.write()

    def lookup_endpoint(self, endpoint):
        reverse_lookup = {v: k for k, v in self.ENDPOINTS.items()}
        return reverse_lookup.get(endpoint)

    def lookup_group(self, group):
        reverse_lookup = {v: k for k, v in self.load_groups().items()}
        return reverse_lookup.get(group)

    @property
    def current(self):
        curr = self.load_option('current')
        if curr is None:
            raise PilotInvalidProject('No current project configured')
        return curr

    @current.setter
    def current(self, value):
        projects = list(self.load_all().keys())
        if value not in projects and value is not None:
            raise ValueError(f'Project must be one of: {", ".join(projects)}')
        self.save_option('current', value)

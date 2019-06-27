import logging
import time
from pilot import config
from pilot.exc import PilotInvalidProject
from pilot.search import gen_gmeta

DEFAULT_PROJECTS = {
    'ncipilot1': {
        'description': 'This is the NCI Pilot Project',
        'title': 'NCI Pilot 1',
        'endpoint': 'ebf55996-33bf-11e9-9fa4-0a06afd4a22e',
        'resource_server': 'petrel_https_server',
        'search_index': '889729e8-d101-417d-9817-fa9d964fdbc9',
        'base_path': '/restricted/dataframes',
        'group': 'd99b3400-33e7-11e9-8857-0af4690c7c7e'
    },
    'ncipilot1-test': {
        'description': 'This is the NCI Pilot Project testing project',
        'title': 'NCI Pilot 1 TEST',
        'endpoint': 'ebf55996-33bf-11e9-9fa4-0a06afd4a22e',
        'resource_server': 'petrel_https_server',
        'search_index': 'e0849c9b-b709-46f3-be21-80893fc1db84',
        'base_path': '/test',
        'group': 'd99b3400-33e7-11e9-8857-0af4690c7c7e'
    },
}

log = logging.getLogger(__name__)


class Project(config.ConfigSection):

    SECTION = 'project'
    DEFAULT_PROJECT = 'ncipilot1'
    PROJECTS_MANIFEST = 'pilot1-tools-project-manifest.json'
    PROJECTS_ENDPOINT = 'ebf55996-33bf-11e9-9fa4-0a06afd4a22e'
    PROJECTS_PATH = '/projects'
    # Cache will go stale in a day
    CACHE_TIMEOUT_SECONDS = 60 * 60 * 24
    ENDPOINTS = {'petrel#ncipilot': 'ebf55996-33bf-11e9-9fa4-0a06afd4a22e'}
    GROUPS = {'NCI Users': 'd99b3400-33e7-11e9-8857-0af4690c7c7e',
              'NCI Admins': '9b54f828-144f-11e9-bf08-0edc9bdd56a6s'}
    PROJECTS_MANIFEST_INDEX = 'e0849c9b-b709-46f3-be21-80893fc1db84'
    DEFAULT_SEARCH_INDEX = 'e0849c9b-b709-46f3-be21-80893fc1db84'
    DEFAULT_RESOURCE_SERVER = 'petrel_https_server'

    def __init__(self, client):
        super().__init__()
        self.client = client
        cfg = self.config.load()
        if not self.load_all():
            cfg['projects'] = DEFAULT_PROJECTS
            self.config.save(cfg)

    def get_manifest_subject(self):
        return 'globus://{}'.format(self.PROJECTS_MANIFEST)

    def update(self, index=None, dry_run=False):
        self.reset_cache_timer()
        sub = self.get_manifest_subject()
        index = index or self.PROJECTS_MANIFEST_INDEX
        sc = self.client.get_search_client()
        new_projects = sc.get_subject(index, sub).data['content'][0]
        if dry_run is False:
            cfg = self.config.load()
            cfg['projects'] = new_projects
            cfg.write()
        return new_projects

    def update_with_diff(self, index=None, dry_run=False):
        old = self.load_all()
        new = self.update(index=index, dry_run=dry_run)
        oldk, newk = set(old.keys()), set(new.keys())
        diff = dict()
        diff['removed'] = {k: old[k] for k in oldk - newk}
        diff['added'] = {k: new[k] for k in newk - oldk}
        diff['changed'] = {}
        for k in oldk.intersection(newk):
            if old[k] != new[k]:
                changed = [pk for pk in set(old[k]) - set(new[k])
                           if old[k][pk] != new[k][pk]]
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
        gmeta = gen_gmeta(sub, ['public'], dict(self.load_all()))
        self.client.ingest_entry(gmeta, index=index)

    def load_all(self):
        return self.config.load().get('projects', {})

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

    def add_project(self, slug, project_data):
        cfg = self.config.load()
        cfg['projects'][slug] = project_data
        cfg.write()

    def lookup_endpoint(self, endpoint):
        reverse_lookup = {v: k for k, v in self.ENDPOINTS.items()}
        return reverse_lookup.get(endpoint)

    def lookup_group(self, group):
        reverse_lookup = {v: k for k, v in self.GROUPS.items()}
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
        if value not in projects:
            raise ValueError(f'Project must be one of: {", ".join(projects)}')
        self.save_option('current', value)

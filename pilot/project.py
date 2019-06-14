import logging
import time
from pilot import config
from pilot.exc import PilotInvalidProject

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
    DEFAULT_PATH = '/test/pilot1-tools-manifest.json'
    # Cache will go stale in a day
    CACHE_TIMEOUT_SECONDS = 60 * 60 * 24

    def __init__(self, client):
        super().__init__()
        self.client = client
        cfg = self.config.load()
        if not self.load_all():
            cfg['projects'] = DEFAULT_PROJECTS
            self.config.save(cfg)

    def update(self, project=None, path=None, dry_run=False):
        self.reset_cache_timer()
        http_cli = self.client.get_http_client(project or self.DEFAULT_PROJECT)
        projects = http_cli.get(path or self.DEFAULT_PATH).data
        if dry_run is False:
            cfg = self.config.load()
            cfg['projects'] = projects
            cfg.write()
        return projects

    def update_with_diff(self, project=None, path=None, dry_run=False):
        old = self.load_all()
        new = self.update(project, path, dry_run)
        oldk, newk = set(old.keys()), set(new.keys())
        diff = dict()
        diff['removed'] = {k: old[k] for k in oldk - newk}
        diff['added'] = {k: new[k] for k in newk - oldk}
        diff['changed'] = {}
        for k in oldk.intersection(newk):
            if old[k] != new[k]:
                changed = [pk for pk in set(old[k]) + set(new[k])
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

    def push(self, project=None, path=None):
        http_cli = self.client.get_http_client(project or self.DEFAULT_PROJECT)
        files = {
            'file': ('report.csv', 'some,data,to,send\nanother,row,to,send\n')
        }
        files.keys()
        raise NotImplementedError()

        http_cli.put(path or self.DEFAULT_PATH)

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
            return bool(self.current)
        except PilotInvalidProject:
            return False

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

import logging
from pilot import config
from pilot.exc import PilotInvalidProject

log = logging.getLogger(__name__)


class Project(config.ConfigSection):

    SECTION = 'project'

    def load_all(self):
        return self.config.load().get('projects', {})

    def load_groups(self):
        return dict(self.config.load().get('groups', {}))

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

    def set_project(self, slug):
        self.current = slug

    def add_project(self, slug, project_data):
        cfg = self.config.load()
        cfg['projects'][slug] = project_data
        cfg.write()

    def delete_project(self, slug):
        if self.current == slug:
            self.current = None
        cfg = self.config.load()
        del cfg['projects'][slug]
        cfg.write()

    def lookup_group(self, group):
        reverse_lookup = {v: k for k, v in self.load_groups().items()}
        return reverse_lookup.get(group)

    def purge(self):
        cfg = self.config.load()
        cfg['projects'] = {}
        cfg['groups'] = {}
        cfg['project']['current'] = ''
        cfg.write()

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

import time
import copy
import logging
import globus_sdk
from pilot import config, exc
from pilot.search import gen_gmeta

log = logging.getLogger(__name__)

# Timeout for when to check for project updates (Default 24 hours)
DEFAULT_PROJECTS_CACHE_TIMEOUT = 60 * 60 * 24


DEFAULT_PILOT_CONTEXT = {
    'client_id': 'e4d82438-00df-4dbd-ab90-b6258933c335',
    'app_name': 'Globus Pilot',
    'manifest_index': None,
    'manifest_subject': 'globus://project-manifest.json',
    'scopes': [
        'profile',
        'openid',
        'urn:globus:auth:scope:search.api.globus.org:all',
        'urn:globus:auth:scope:transfer.api.globus.org:all',
        'https://auth.globus.org/scopes/'
        '56ceac29-e98a-440a-a594-b41e7a084b62/all',
    ],
    'projects_cache_timeout': DEFAULT_PROJECTS_CACHE_TIMEOUT,
    'projects_endpoint': '',
    'projects_base_path': '',
    'projects_group': '',
    'projects_default_search_index': None,
    'projects_default_resource_server': 'petrel_https_server',
}


class Context(config.ConfigSection):

    SECTION = 'context'
    DEFAULT_CONTEXT = 'candle-pilot1'

    def __init__(self, client, *args, index_uuid=None, **kwargs):
        self.client = client
        self._current = None
        super().__init__(*args, **kwargs)
        if index_uuid:
            display_name = self.add_context_by_uuid(index_uuid)
            self.current = display_name
            self.update()

    @property
    def current(self):
        curr = self.load_option('current') or self._current
        if curr is None:
            raise exc.PilotContextException('No current context configured')
        return curr

    @current.setter
    def current(self, value):
        contexts = self.load_option('contexts') or {}
        ctx_names = list(contexts.keys())
        if ctx_names and value not in ctx_names and value is not None:
            raise ValueError(f'Context must be one of: {", ".join(contexts)}')
        self.save_option('current', value)

    def load_all(self):
        return self.config.load().get('contexts', {})

    def add_context_by_uuid(self, index_uuid):
        ctx = copy.deepcopy(DEFAULT_PILOT_CONTEXT)
        index_info = self.get_index(index_uuid)
        display_name = index_info['display_name']
        ctx['manifest_index'] = index_uuid
        self.add_context(display_name, ctx)
        return display_name

    def add_context(self, name, context):
        ctx = copy.deepcopy(DEFAULT_PILOT_CONTEXT)
        ctx.update(context)
        self.save_option(name, ctx, section='contexts')

    def get_context(self, context=None):
        return self.load_option(context or self.current, section='contexts')

    def update_context(self, new_context_info, context=None):
        nci_ks = set(new_context_info.keys())
        key_diff = nci_ks.difference(set(DEFAULT_PILOT_CONTEXT.keys()))
        if key_diff:
            raise exc.PilotContextException(f'Invalid context keys set: '
                                            f'{key_diff}')
        ctx_name = context or self.current
        ctx = self.get_context(ctx_name)
        ctx.update(new_context_info)
        self.save_option(ctx_name, ctx, section='contexts')

    def set_context(self, context):
        if self.current == context:
            return
        self.current = context
        self.update()

    def get_value(self, field, context=None):
        return self.get_context(context).get(field)

    def get_index(self, index_uuid):
        return self.get_search_client().get_index(index_uuid).data

    def get_search_client(self):
        try:
            sc = self.client.get_search_client()
        except Exception:
            log.debug('Failed to get authenticated search client, '
                      'fetching unauthenticated one instead.', exc_info=True)
            sc = globus_sdk.SearchClient()
        return sc

    def update(self, index=None, dry_run=False, update_groups_cache=True):
        """Update the local list of projects and groups."""
        self.reset_cache_timer()
        sub = self.get_value('manifest_subject')
        index = index or self.get_value('manifest_index')
        log.debug('Fetching manifest {} from index {}'.format(sub, index))
        try:
            sc = self.get_search_client()
            result = sc.get_subject(index, sub,
                                    result_format_version='2019-08-27')
            manifest = result.data['entries'][0]['content']
        except globus_sdk.exc.SearchAPIError as sapie:
            if sapie.code == 'NotFound.Generic':
                self.client.project.purge()
                raise exc.NoManifestException(
                    'No existing context data found for {}.'
                    ''.format(self.get_value('manifest_subject')))
            else:
                log.debug('Encountered error updating context',
                          exc_info=True)
                raise exc.PilotClientException('Unexpected Error {}'.format(
                    str(sapie)))
        if dry_run is False:
            log.debug('Writing fresh context to config.')
            cfg = self.config.load()
            index_name = sc.get_index(index).data['display_name']
            context = manifest.get('context')
            if context:
                cfg['contexts'][index_name] = context
            cfg['projects'] = manifest.get('projects', {})
            cfg['groups'] = manifest.get('groups', {})
            cfg.write()
        return manifest

    def update_with_diff(self, index=None, dry_run=False,
                         update_groups_cache=True):
        new = self.update(index=index, dry_run=dry_run,
                          update_groups_cache=update_groups_cache)
        projects = self.client.project.load_all()
        groups = self.client.project.load_groups()
        return {
            'context': self.get_diff(self.get_context(),
                                     new.get('context', {})),
            'projects': self.get_diff(projects, new.get('projects', {})),
            'groups': self.get_diff(groups, new.get('groups', {}))
        }

    def get_diff(self, old, new):
        """Fetch the differences between two dictionaries. Dicts can be one
        or two levels deep, for example:
        old: {'foo': 'bar'}, new: {'foo': 'moo'}
        OR
        old: {'foo': {'bar': 'baz'}, new: {'foo': {'bar': 'moo'}
        """
        oldk, newk = set(old.keys()), set(new.keys())
        diff = dict()
        diff['removed'] = {k: old[k] for k in oldk - newk}
        diff['added'] = {k: new[k] for k in newk - oldk}
        diff['changed'] = {}
        for k in oldk.intersection(newk):
            if old[k] != new[k]:
                if isinstance(old[k], str):
                    diff['changed'][k] = '"{}" changed to "{}"'.format(old[k],
                                                                       new[k])
                else:
                    changed = [pk for pk in set(old[k]).union(set(new[k]))
                               if old[k].get(pk) != new[k].get(pk)]
                    changed_str = [f'{old[k].get(c)} --> {new[k].get(c)}'
                                   for c in changed]
                    diff['changed'][k] = dict(zip(changed, changed_str))
        return {k: v for k, v in diff.items() if v}

    def reset_cache_timer(self):
        self.save_option('last_update', int(time.time()))

    def is_cache_stale(self):
        if not self.get_context():
            return True
        last_updated = self.load_option('last_update')
        if last_updated:
            cfg_timeout = int(
                self.get_value('projects_cache_timeout'))
            if time.time() < int(last_updated) + cfg_timeout:
                return False
        return True

    def push(self, context=None):
        context_info = self.get_context(context or self.current)
        manifest = {
            'projects': dict(self.client.project.load_all()),
            'groups': dict(self.client.project.load_groups()),
            'context': dict(context_info)
        }
        gmeta = gen_gmeta(context_info['manifest_subject'], ['public'],
                          manifest, validate=False)
        self.client.ingest_gmeta(gmeta, index=context_info['manifest_index'])

    def fetch_subgroups(self, group=None):
        nc = self.client.get_nexus_client()
        if nc is not None:
            ctx_group = self.get_value('projects_group')
            resp = nc.get_subgroups(group or ctx_group)
            return resp.data.json().get('children')
        return []

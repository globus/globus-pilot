import sys
import logging
import click
import globus_sdk

from pilot import exc, commands

log = logging.getLogger(__name__)


class InputValidator:

    def __init__(self, queries=None, order=None):

        self.queries = queries or {}
        self.order = order or sorted(self.queries.keys())
        if not set(order) == set(queries.keys()):
            raise ValueError('Order given must match number of queries: \n'
                             f'Queries: {set(queries)}\nOrder: {set(order)}')
        self.answers = {}

    def ask(self, query, info):
        default = info.get('default')
        if callable(default):
            default = default(self, query)
        user_input = input(f'{info["prompt"]} ({default})> ') or default
        if user_input == 'help':
            click.echo(info['help'])
            return self.ask(query, info)
        if user_input == 'q':
            click.secho('Exiting...', fg='red')
            sys.exit(-1)
        try:
            for validate in info.get('validation', []):
                validate(self, user_input)
            self.answers[query] = user_input
            return user_input
        except exc.PilotValidator as iv:
            click.secho(iv.message, fg='yellow')
            return self.ask(query, info)

    def ask_all(self):
        click.secho(f'{len(self.queries)} items to set. Type "help" for more '
                    f'information or "q" to quit.', fg='blue')
        for query in self.order:
            self.ask(query, self.queries[query])
        click.echo('Summary:')
        for subject, answer in self.answers.items():
            title = self.queries[subject].get('title', subject)
            click.echo('{:20.19}{}'.format(title, answer))
        if input('Continue with these values? (y/n)') != 'y':
            for k, v in self.answers.items():
                self.queries[k]['default'] = v
            return self.ask_all()
        return self.answers


def validate_no_spaces(v, string):
    if ' ' in string:
        raise exc.PilotValidator(f'"{string}" cannot contain spaces')


def validate_project_title_unique(v, title):
    pc = commands.get_pilot_client()
    titles = [p['title'] for p in pc.project.load_all().values()]
    if title in titles:
        raise exc.PilotValidator('Title must be unique from '
                                 f'{", ".join(titles)}')


def validate_project_slug_unique(v, slug):
    pc = commands.get_pilot_client()
    slugs = pc.project.load_all().keys()
    if slug in slugs:
        raise exc.PilotValidator(f'Slug must be unique from {", ".join(slug)}')


def validate_slug_to_path_unique(v, slug):
    pc = commands.get_pilot_client()
    tc = pc.get_transfer_client()
    try:
        path = commands.path_utils.slug_to_path(slug)
        response = tc.operation_ls(pc.project.PROJECTS_ENDPOINT,
                                   path=pc.project.PROJECTS_PATH)
        existing = [f['name'] for f in response.data['DATA']]
        if path in existing:
            raise exc.PilotValidator('"{}" is not available, please choose '
                                     'another'.format(slug))
    except globus_sdk.exc.TransferAPIError as tapie:
        log.exception(tapie.message)
        raise exc.PilotValidator('An error occurred, please try a different '
                                 'value or notify a system administrator.')


def validate_project_endpoint(v, ep):
    pc = commands.get_pilot_client()
    if ep not in pc.project.ENDPOINTS.keys():
        raise exc.PilotValidator('Endpoint must be one of: "{}"'.format(
            ', '.join(pc.project.ENDPOINTS.keys())
        ))


def validate_project_group(v, group):
    pc = commands.get_pilot_client()
    valid_choices = list(pc.project.GROUPS.keys()) + ['None']
    if group not in valid_choices:
        raise exc.PilotValidator('Group must be one of: '
                                 '{}'.format(', '.join(valid_choices)))


def validate_project_path_unique(v, path):
    pc = commands.get_pilot_client()
    paths = [p['base_path'] for p in pc.project.load_all().values()]
    if path in paths:
        raise exc.PilotValidator('Path must be unique. (Other paths include '
                                 f'{", ".join(paths)})')

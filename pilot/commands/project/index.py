import logging
import uuid
import sys
import click

from fair_research_login import ScopesMismatch

from pilot import commands, exc
from pilot.commands.project.project import project_command
from pilot.context import DEFAULT_PROJECTS_CACHE_TIMEOUT
from pilot.commands import input_validation

log = logging.getLogger(__name__)


@click.group(name='index', help='Set or display index information',
             invoke_without_command=True)
@click.pass_context
def index_command(ctx):
    pc = commands.get_pilot_client()

    if ctx.invoked_subcommand is None:
        click.echo('Set index with "pilot index set <index_uuid>|'
                   '<index_name>"')
        contexts = pc.context.load_all()
        fmt = '{} {}'
        for context in contexts:
            if context == pc.context.current:
                click.secho(fmt.format('*', context), fg='green')
            else:
                click.echo(fmt.format(' ', context))


@index_command.command(help='Set Pilot to use a different search index',
                       name='set')
@click.argument('index_name')
@click.pass_context
def set_index(ctx, index_name):
    pc = commands.get_pilot_client()
    if not pc.context.get_context(index_name):
        log.debug(f'No local context "{index_name}", attempting lookup...')
        try:
            # Ensure we're using the index UUID, lookup by name is no longer
            # possible
            uuid.UUID(index_name)
            index_uuid = index_name

            click.secho('looking up {}...'.format(index_uuid))
            sc = pc.get_search_client()
            index_info = sc.get_index(index_uuid)
            display_name = index_info['display_name']
            pc.context.add_context(display_name, {
                'client_id': 'e4d82438-00df-4dbd-ab90-b6258933c335',
                'app_name': '{} app'.format(display_name),
                'manifest_index': index_uuid,
                'manifest_subject': 'globus://project-manifest.json',
                'scopes': pc.DEFAULT_SCOPES,
                'projects_cache_timeout': DEFAULT_PROJECTS_CACHE_TIMEOUT,
                'projects_endpoint': '',
                'projects_base_path': '',
                'projects_group': '',
                'projects_default_search_index': index_uuid,
                'projects_default_resource_server': 'petrel_https_server',
            })
            index_name = display_name
        except ValueError:
            click.secho(f'"{index_name}": must be a UUID when adding a new '
                        f'un-tracked search index.', fg='red')
            sys.exit(1)
        except Exception as e:
            log.exception(e)
            click.secho('Unable to find index {}'.format(index_name))
            sys.exit(2)
    pc.context.set_context(index_name)
    try:
        log.debug('Updating index...')
        pc.context.update()
    except exc.NoManifestException:
        click.secho('Pilot has not been setup for this index. Run '
                    '"pilot index setup" to do so.', fg='red')
        sys.exit(3)

    # If there is only one project, automatically set pilot to that one
    if len(pc.project.load_all()) == 1:
        projects = pc.project.load_all()
        pc.project.current = list(projects.keys())[0]
    log.debug('Context set! Fetching general info for user...')
    ctx.invoke(info, index=index_name)
    ctx.invoke(project_command)
    try:
        pc.load_tokens(requested_scopes=pc.context.get_value('scopes'))
    except ScopesMismatch:
        click.secho('Scopes do not match for this index, please login '
                    'again.', fg='red')
    log.debug(pc.context.get_value('projects_default_search_index'))
    if not pc.project.load_all():
        example = '''
        [[default-project]]
        base_path = /
        description =
        endpoint =
        group =
        resource_server = petrel_https_server
        search_index = {}
        title = default-project
        '''.format(pc.context.get_value('projects_default_search_index'))
        click.secho('No projects in this index, you can bootstrap one in the '
                    'config under [projects]\n{}'.format(example))


@index_command.command(help='Print Info for index')
@click.argument('index', required=False)
def info(index=None):
    pc = commands.get_pilot_client()
    index = index or pc.context.current
    if index is None:
        click.echo('Use "pilot index info <context>" to list info about a '
                   'project.')
        return
    try:
        info = pc.context.get_context(index)
    except exc.PilotInvalidProject as pip:
        click.secho(str(pip), fg='red')
        return

    fmt = '{:40.39}{}'
    log.debug(info)
    output = '\n'.join([fmt.format(*i) for i in info.items()])
    click.echo(output)
    click.echo()


@index_command.command(help='Setup pilot on a search index')
def setup():
    """Setup a brand new pilot config for a new index.

    NOTE: Paths with tilde '~' DO NOT WORK. These cause problems for resolving
    paths that look like /~/foo/bar, which sometimes translate as ~/foo/bar
    instead. These are disabled to prevent that from happening.
    """
    PROJECT_QUERIES = {
        'projects_endpoint': {
            'prompt': 'Set a Globus UUID where your data should be stored.',
            'default': '',
            'help': 'visit "https://app.globus.org/file-manager/collections" '
                    'to find Globus endpoint to store your data.',
            'validation': [input_validation.validate_is_uuid,
                           input_validation.validate_is_globus_endpoint],
        },
        'projects_base_path': {
            'prompt': 'Pick a base path.',
            'default': '/',
            'help': 'All data will be saved under this directory',
            'validation': [input_validation.validate_no_spaces,
                           input_validation.validate_absolute_path,
                           input_validation.validate_no_tilde],
        },
        'projects_group': {
            'prompt': 'Pick a Globus Group to secure Globus Search records',
            'default': 'public',
            'help': 'The group determines who can view records in search. '
                    'People not in this group will not see records in Globus '
                    'Search. "public" allows anyone to see these records.',
            'validation': [input_validation.validate_is_valid_globus_group],
        },
    }
    pc = commands.get_pilot_client()
    projects = pc.project.load_all().keys()
    if projects:
        click.secho(
            f'Index is already setup with the following projects: {projects}. '
            f'Please delete them before setting up your index.', fg='red')
        return
    order = ['projects_endpoint', 'projects_base_path', 'projects_group']

    iv = input_validation.InputValidator(queries=PROJECT_QUERIES, order=order)
    new_ctx = iv.ask_all()
    pc.context.update_context(new_ctx)
    pc.context.push()
    click.secho('Your index has been setup successfully. Now see '
                '`pilot project add`.', fg='green')
    return


@index_command.command(help='Update a context')
def push():
    pc = commands.get_pilot_client()
    pc.context.push()
    click.secho('Global projects have been updated. Users will be notified '
                'within 24 hours.', fg='green')

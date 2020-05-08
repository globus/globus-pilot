import logging
import click

from fair_research_login import ScopesMismatch

from pilot import commands, exc
from pilot.context import DEFAULT_PROJECTS_CACHE_TIMEOUT

log = logging.getLogger(__name__)


@click.group(name='context', help='Set or display context information',
             invoke_without_command=True, hidden=True)
@click.pass_context
def context_command(ctx):
    pc = commands.get_pilot_client()

    if ctx.invoked_subcommand is None:
        click.echo('Set project with "pilot project set <myproject>"')
        contexts = pc.context.load_all()
        fmt = '{} {}'
        for context in contexts:
            if context == pc.context.current:
                click.secho(fmt.format('*', context), fg='green')
            else:
                click.echo(fmt.format(' ', context))


@context_command.command(help='Update stored list of projects.', name='set')
@click.argument('index_name', required=False)
# @click.option('-u', '--index-uuid', 'index_uuid', help='Use this index uuid')
@click.pass_context
def set_context(ctx, index_name):
    pc = commands.get_pilot_client()
    if not pc.context.get_context(index_name):
        try:
            click.secho('looking up {}...'.format(index_name))
            sc = pc.get_search_client()
            index_uuid = sc.get_index(index_name).data['id']
            pc.context.add_context(index_name, {
                'client_id': 'e4d82438-00df-4dbd-ab90-b6258933c335',
                'app_name': '{} app'.format(index_name),
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
        except Exception as e:
            log.exception(e)
            click.secho('Unable to find index {}'.format(index_name))
            return
    pc.context.set_context(index_name)
    pc.context.update()
    ctx.invoke(info, context=index_name)
    ctx.invoke(commands.project.project.project_command)
    try:
        pc.load_tokens(requested_scopes=pc.context.get_value('scopes'))
        click.secho('Current credentials are sufficient, no need to login '
                    'again.', fg='green')
    except ScopesMismatch:
        click.secho('Scopes do not match for this context, please login '
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


@context_command.command(help='Print Context Details')
@click.argument('context', required=False)
def info(context=None):
    pc = commands.get_pilot_client()
    context = context or pc.context.current
    if context is None:
        click.echo('Use "pilot context info <context>" to list info about a '
                   'project.')
        return
    try:
        info = pc.context.get_context(context)
    except exc.PilotInvalidProject as pip:
        click.secho(str(pip), fg='red')
        return

    fmt = '{:40.39}{}'
    log.debug(info)
    output = '\n'.join([fmt.format(*i) for i in info.items()])
    click.echo(output)
    click.echo()


@context_command.command(help='Update a context')
def push():
    pc = commands.get_pilot_client()
    pc.context.push()
    click.secho('Global projects have been updated. Users will be notified '
                'within 24 hours.', fg='green')

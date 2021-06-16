import os
import sys
import logging
import click
from slugify import slugify
import globus_sdk

from pilot import commands, exc
from pilot.commands import input_validation

log = logging.getLogger(__name__)

PROJECT_QUERIES = {
    'title': {
        'prompt': 'Pick a title for your new project',
        'default': 'My New Project',
        'help': 'Pick something short and easy to remember',
        'validation': [input_validation.validate_project_title_unique],
    },
    'short_name': {
        'prompt': 'Pick a short name, this will create a directory on "{}" to '
                  'store your files.',
        'default': lambda v, q: slugify(v.answers['title']),
        'help': 'The short name will be used in URLs and will be the name '
                'users select this new project',
        'validation': [input_validation.validate_no_spaces,
                       input_validation.validate_project_slug_unique,
                       input_validation.validate_slug_to_path_unique],
    },
    'description': {
        'prompt': 'Describe your new project',
        'default': 'This project is intended to do X for scientists',
        'help': 'A nice description can help people understand what your '
                'project does, at a glance',
        'validation': [],
    },
}


@click.group(name='project', help='Set or display project information',
             invoke_without_command=True)
@click.pass_context
def project_command(ctx):
    pc = commands.get_pilot_client()
    if not pc.is_logged_in():
        click.echo('You are not logged in.')
        return
    invalid_with_pending_update = ['delete', 'add']
    if ctx.invoked_subcommand in invalid_with_pending_update:
        if any(pc.context.update_with_diff(dry_run=True).values()):
            click.secho('There is an update for projects, please update '
                        '("pilot project update") before adding a new project',
                        fg='red')
            sys.exit()
    if ctx.invoked_subcommand is None:
        click.echo('Set project with "pilot project set <myproject>"')
        projects = pc.project.load_all()
        current = pc.project.current if pc.project.is_set() else None
        fmt = '{} {}'
        for project in projects:
            if project == current:
                click.secho(fmt.format('*', project), fg='green')
            else:
                click.echo(fmt.format(' ', project))


@project_command.command(help='Update stored list of projects.')
@click.option('--dry-run', is_flag=True, default=False)
@click.option('--update-groups-cache/--no-update-groups-cache', default=True,
              help='Fetch the latest subgroups from Globus')
def update(dry_run, update_groups_cache):
    pc = commands.get_pilot_client()
    try:
        output = pc.context.update_with_diff(
            dry_run=dry_run, update_groups_cache=update_groups_cache)
        if not any(output.values()):
            click.secho('Project is up to date', fg='green')
            return
        for group, changes in output.items():
            if not changes:
                continue
            click.echo('{}:'.format(group))
            for change_type, items in changes.items():
                click.echo('\t{}:'.format(change_type))
                for name, value in items.items():
                    click.echo('\t\t{} -> {}'.format(name, value))
    except globus_sdk.exc.SearchAPIError as sapie:
        click.secho(str(sapie), fg='red')
        click.secho('You can create the manifest for this index with `pilot '
                    'context push`', fg='blue')


@project_command.command(name='set', help='Set your project')
@click.argument('project', required=True)
def set_command(project):
    pc = commands.get_pilot_client()
    try:
        pc.project.current = project
        click.echo(f'Current project set to {project}')
    except ValueError as ve:
        click.secho(str(ve), fg='red')


@project_command.command(help='Add a new project')
def add():
    pc = commands.get_pilot_client()
    order = ['title', 'short_name', 'description']
    base_path = pc.context.get_value('projects_base_path')
    PROJECT_QUERIES['short_name']['prompt'] = \
        PROJECT_QUERIES['short_name']['prompt'].format(base_path)
    titles = [p['title'] for p in pc.project.load_all().values()]
    PROJECT_QUERIES['title']['current'] = titles

    iv = input_validation.InputValidator(queries=PROJECT_QUERIES, order=order)
    project = iv.ask_all()
    project.update(
        {'search_index': pc.context.get_value('projects_default_search_index'),
         'resource_server':
            pc.context.get_value('projects_default_resource_server')}
    )
    project['endpoint'] = pc.context.get_value('projects_endpoint')
    project['group'] = pc.context.get_value('projects_group')
    short_name = project.pop('short_name')
    project['base_path'] = os.path.join(base_path, short_name)

    click.secho('Updating global project list... ', nl=False)
    pc.project.add_project(short_name, project)
    tc = pc.get_transfer_client()
    tc.operation_mkdir(project['endpoint'], project['base_path'])
    pc.context.push()
    click.secho('Success', fg='green')
    pc.project.set_project(short_name)
    click.secho('Switched to project {}'.format(short_name))
    click.secho('Your new project "{}" has been added! '
                'Users will be notified within 24 hours next time they use '
                'this tool.'.format(project['title']), fg='green')


@project_command.command(help='Print project details')
@click.argument('project', required=False)
def info(project=None):
    pc = commands.get_pilot_client()
    current = pc.project.current if pc.project.is_set() else None
    project = project or current
    if project is None:
        click.echo('Use "pilot project info <project>" to list info about a '
                   'project.')
        return
    try:
        info = pc.project.get_info(project)
    except exc.PilotInvalidProject as pip:
        click.secho(str(pip), fg='red')
        return

    ep_name = info['endpoint']
    try:
        tc = pc.get_transfer_client()
        ep = tc.get_endpoint(info['endpoint']).data
        ep_name = ep['display_name'] or ep['canonical_name'] or ep_name
    except globus_sdk.exc.TransferAPIError:
        click.echo('Failed to lookup endpoint {}, please ensure it is active.'
                   .format(info['endpoint']))

    dinfo = [
        (info['title'], ''),
        ('Endpoint', ep_name),
        ('Group', pc.project.lookup_group(info['group'])),
        ('Base Path', info['base_path']),
    ]

    fmt = '{:25.24}{}'
    log.debug(info)
    output = '\n'.join([fmt.format(*i) for i in dinfo])
    click.echo(output)
    click.echo()
    click.echo(info['description'])


@project_command.command(help='Delete a project')
@click.option('--keep-context', is_flag=True, default=False,
              help='Continue to track the empty project in pilot after delete')
@click.argument('project', required=True)
def delete(project, keep_context):
    pc = commands.get_pilot_client()
    if project not in pc.project.load_all():
        click.secho('{} is not a valid project'.format(project), fg='red')
        return 1
    pc.project.current = project
    results = pc.search(project=project)
    pinfo = pc.project.get_info(project)
    search_query = {
        'q': '*',
        'filters': {
            'field_name': 'project_metadata.project-slug',
            'type': 'match_all',
            'values': [project or pc.project.current]
        }
    }
    project_base_path = pc.get_path('', project=project)
    search_client = pc.get_search_client()
    transfer_client = pc.get_transfer_client()
    log.debug('Base path for delete is: {}'.format(project_base_path))
    dz = '\n{}\nDANGER ZONE\n{}'.format('/' * 80, '/' * 80)
    click.secho('{dz}\n'
                'This will delete all data and search results in your '
                'project.\n{tot} datasets will be deleted for {project}\n\n'
                'Base Directory "{project_base_path}" will be deleted.'
                '{dz}'
                ''.format(dz=dz, tot=results['total'], project=project,
                          project_base_path=project_base_path),
                bg='red')
    click.echo('Please type the name ({}) of your project to delete it> '
               .format(project), nl=False)
    if input() != project:
        click.secho('Names do not match, aborting...')
        return 1
    click.echo(f'Deleting Data: {project_base_path}')
    try:
        ddata = globus_sdk.DeleteData(transfer_client, pinfo['endpoint'],
                                      recursive=True,
                                      notify_on_succeeded=False)
        ddata.add_item(project_base_path)
        transfer_client.submit_delete(ddata)
    except globus_sdk.exc.TransferAPIError as tapie:
        log.debug('Error deleting base folder', exc_info=tapie)
        click.secho(f'Error deleting project base folder {project_base_path}: '
                    f'{str(tapie)}', fg='red')

    try:
        click.echo(f'Deleting Search Records: {pinfo["search_index"]}')
        log.debug(f'Search Query: {search_query}')
        search_client.delete_by_query(pinfo['search_index'], search_query)
    except globus_sdk.exc.SearchAPIError as sapie:
        log.debug('Error deleting test data', exc_info=sapie)
        click.secho(f'Error deleting search data {pinfo["search_index"]}: '
                    f'{str(sapie)}', fg='red')
    if keep_context:
        click.secho('Keeping now empty pilot project {}'.format(project),
                    fg='blue')
        pc.mkdir('/')
    else:
        click.echo('Removing project...')
        pc.project.delete_project(project)
        pc.context.push()
    click.secho('Project {} has been deleted successfully.'.format(project),
                fg='green')


@project_command.command(help='Edit items about your project')
@click.argument('project', required=False)
def edit(project=None):
    pc = commands.get_pilot_client()
    current = pc.project.current if pc.project.is_set() else None
    project = project or current
    if project is None:
        click.echo('Use "pilot project info <project>" to list info about a '
                   'project.')
        return
    info = pc.project.get_info(project)
    queries = {'title': PROJECT_QUERIES['title'].copy(),
               'description': PROJECT_QUERIES['description'].copy()}
    titles = [p['title'] for p in pc.project.load_all().values()
              if p['title'] != info['title']]
    queries['title']['current'] = titles

    for key in queries:
        queries[key]['default'] = info[key]
    iv = input_validation.InputValidator(queries=queries,
                                         order=['title', 'description'])
    new_info = iv.ask_all()
    info.update(new_info)
    pc.project.set_project(project, info)
    pc.context.push()
    click.secho('Project "{}" has been updated'.format(project), fg='green')


@project_command.command(help='Update the global list of projects',
                         hidden=True)
def push():
    pc = commands.get_pilot_client()
    pc.context.push()
    click.secho('Global projects have been updated. Users will be notified '
                'within 24 hours.', fg='green')

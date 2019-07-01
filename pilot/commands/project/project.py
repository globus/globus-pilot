import os
import sys
import logging
import click
from slugify import slugify
import globus_sdk

from pilot import commands, exc
from pilot.commands import input_validation, path_utils, search

log = logging.getLogger(__name__)

ADD_PROJECT_QUERIES = {
    'title': {
        'prompt': 'Pick a title for your new project',
        'default': 'My New Project',
        'help': 'Pick something short and easy to remember',
        'validation': [input_validation.validate_project_title_unique],
    },
    'short_name': {
        'prompt': 'Pick a short name',
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
    'group': {
        'prompt': 'Set your Globus Group',
        'default': 'NCI Users',
        'help': 'The group determines who has read/write access to files, '
                'and who can view records in search',
        'validation': [input_validation.validate_project_group],
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
        if any(pc.project.update_with_diff(dry_run=True).values()):
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
def update(dry_run):
    pc = commands.get_pilot_client()
    try:
        output = pc.project.update_with_diff(dry_run=dry_run)
        if not any(output.values()):
            click.secho('Project is up to date', fg='green')
            return
        for k, v in output.items():
            click.echo(k)
            for item in v:
                click.echo(f'\t{item}')
    except exc.HTTPSClientException as hce:
        click.secho(str(hce), fg='red')


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
    order = ['title', 'short_name', 'description', 'group']
    queries = {
        'title': {
            'prompt': 'Pick a title for your new project',
            'default': 'My New Project',
            'help': 'Pick something short and easy to remember',
            'validation': [input_validation.validate_project_title_unique],
        },
        'short_name': {
            'prompt': 'Pick a short name',
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
        'group': {
            'prompt': 'Set your Globus Group',
            'default': 'NCI Users',
            'help': 'The group determines who has read/write access to files, '
                    'and who can view records in search',
            'validation': [input_validation.validate_project_group],
        },
    }
    iv = input_validation.InputValidator(queries=queries, order=order)
    project = iv.ask_all()
    project.update({'search_index': pc.project.DEFAULT_SEARCH_INDEX,
                    'resource_server': pc.project.DEFAULT_RESOURCE_SERVER})
    project['endpoint'] = pc.project.PROJECTS_ENDPOINT
    project['group'] = pc.project.GROUPS.get(project['group'], 'public')
    short_name = project.pop('short_name')
    project['base_path'] = os.path.join(
        pc.project.PROJECTS_PATH,
        short_name
    )

    click.secho('Updating global project list... ', nl=False)
    pc.project.set_project(short_name, project)
    tc = pc.get_transfer_client()
    tc.operation_mkdir(project['endpoint'], project['base_path'])
    pc.project.push()
    click.secho('Success', fg='green')
    pc.project.current = short_name
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
    info = pc.project.get_info(project)
    dinfo = [
        (info['title'], ''),
        ('Endpoint', pc.project.lookup_endpoint(info['endpoint'])),
        ('Group', pc.project.lookup_endpoint(info['group'])),
        ('Base Path', info['base_path']),
    ]

    fmt = '{:25.24}{}'
    log.debug(info)
    output = '\n'.join([fmt.format(*i) for i in dinfo])
    click.echo(output)
    click.echo()
    click.echo(info['description'])


@project_command.command(help='Delete a project')
@click.argument('project', required=True)
def delete(project):
    pc = commands.get_pilot_client()
    if project not in pc.project.load_all():
        click.secho('{} is not a valid project'.format(project), fg='red')
        return 1
    results = search.search_commands.search_by_project(project=project)
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
    click.secho('{dz}\nThis will delete all data and search results in your'
                'project.\n{tot} datasets will be deleted for {project}'
                '{dz}'.format(dz=dz, tot=results['total'], project=project),
                bg='red')
    click.echo('Please type the name ({}) of your project to delete it> '
               .format(project), nl=False)
    if input() != project:
        click.secho('Names do not match, aborting...')
        return 1
    click.echo('Deleting Data...')
    ddata = globus_sdk.DeleteData(transfer_client, pinfo['endpoint'],
                                  recursive=True, notify_on_succeeded=False)
    ddata.add_item(project_base_path)
    transfer_client.submit_delete(ddata)
    click.echo('Deleting Search Records...')
    search_client.delete_by_query(pinfo['search_index'], search_query)
    click.echo('Removing project...')
    pc.project.delete_project(project)
    pc.project.push()
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
    queries = {'title': ADD_PROJECT_QUERIES['title'].copy(),
               'description': ADD_PROJECT_QUERIES['description'].copy()}
    for key in queries:
        queries[key]['default'] = info[key]
    iv = input_validation.InputValidator(queries=queries,
                                         order=['title', 'description'])
    new_info = iv.ask_all()
    info.update(new_info)
    pc.project.set_project(project, info)
    pc.project.push()
    click.secho('Project "{}" has been updated'.format(project), fg='green')


@project_command.command(help='Update the global list of projects')
def push():
    pc = commands.get_pilot_client()
    pc.project.push()
    click.secho('Global projects have been updated. Users will be notified '
                'within 24 hours.', fg='green')

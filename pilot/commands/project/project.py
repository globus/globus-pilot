import logging
import click

import pilot


log = logging.getLogger(__name__)


@click.group(name='project', help='Set or display project information',
             invoke_without_command=True)
@click.pass_context
def project(ctx):
    pc = pilot.commands.get_pilot_client()
    if ctx.invoked_subcommand is None:
        click.echo('Set project with "pilot project set myproject"')
        projects = pc.project.load_all()
        fmt = '{} {}'
        for project in projects:
            if project == pc.project.current:
                click.secho(fmt.format('*', project), fg='green')
            else:
                click.echo(fmt.format(' ', project))


@project.command()
@click.option('--dry-run', is_flag=True, default=False,
              help='Update stored list of projects.')
def update(dry_run):
    pc = pilot.commands.get_pilot_client()
    try:
        output = pc.project.update_with_diff(dry_run=dry_run)
        if not output:
            click.secho('Project is up to date', fg='green')
        for k, v in output.items():
            click.echo(k)
            for item in v:
                click.echo(f'\t{item}')
    except pilot.exc.HTTPSClientException as hce:
        click.secho(str(hce), fg='red')


@project.command(name='set')
@click.argument('project', required=True)
def set_command(project):
    pc = pilot.commands.get_pilot_client()
    try:
        pc.project.current = project
        click.echo(f'Current project set to {project}')
    except ValueError as ve:
        click.secho(str(ve), fg='red')

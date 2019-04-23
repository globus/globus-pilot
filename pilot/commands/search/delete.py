import click
import os
import globus_sdk

from pilot.client import PilotClient


@click.command(name='delete', help='Delete a search entry')
@click.argument('path', type=click.Path())
@click.option('--test', is_flag=True, default=False)
@click.option('--dry-run', is_flag=True, default=False,
              help="Show report, but don't actually delete entry/file")
@click.option('--delete-data', 'delete_data', default=False,
              help='Output as JSON.')
@click.option('--yes', is_flag=True)
def delete_command(path, test, dry_run, delete_data, yes):
    pc = PilotClient()
    if not pc.is_logged_in():
        click.echo('You are not logged in.')
        return

    fname, dirname = os.path.basename(path), os.path.dirname(path)

    sub_url = pc.get_subject_url(fname, dirname, test)
    if dry_run:
        click.secho('Dry Run (No Delete Performed)')
        click.secho('Search Entry: {}'.format(sub_url))
        click.secho('File: {}'.format(pc.get_path(fname, dirname, test)))
        return

    try:
        pc.delete_entry(fname, dirname, test)
        click.secho('Removed {} Successfully'.format(path), fg='green')
    except globus_sdk.exc.SearchAPIError as se:
        if se.code == 'NotFound.Generic':
            click.secho('{} does not exist, or cannot be found at your '
                        'permission level.'.format(path), fg='yellow')
        else:
            click.secho(str(se))

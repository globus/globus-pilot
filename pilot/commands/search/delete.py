import logging
import click
import globus_sdk
import pilot

log = logging.getLogger(__name__)


@click.command(name='delete', help='Delete a search entry')
@click.argument('path', type=click.Path())
@click.option('--entry-id', default='metadata', help=('Delete a specific entry'
              ' within the search subject, or "null" for a null entry id.'))
@click.option('--subject', default=False, help=('Delete the entire subject '
              'comprising all of its associated entry ids'))
@click.option('--test', is_flag=True, default=False)
@click.option('--dry-run', is_flag=True, default=False,
              help="Show report, but don't actually delete entry/file")
@click.option('--delete-data', 'delete_data', default=False,
              help='Output as JSON.')
@click.option('--yes', is_flag=True)
def delete_command(path, entry_id, subject, test, dry_run, delete_data, yes):
    pc = pilot.commands.get_pilot_client()
    if not pc.is_logged_in():
        click.echo('You are not logged in.')
        return

    sub_url = pc.get_subject_url(path)
    if dry_run:
        click.secho('Dry Run (No Delete Performed)')
        click.secho('Search Entry: {}'.format(sub_url))
        click.secho('File: {}'.format(pc.get_path(path, test)))
        return

    try:
        import os
        dir_list = pc.ls(os.path.dirname(path), extended=True)
        dirname, basename = os.path.dirname(path), os.path.basename(path)
        log.debug('Checking if {} in {}'.format(basename, dir_list))

        if os.path.basename(path) not in dir_list:
            click.secho('No file "{}" exists'.format(path), fg='yellow')
            return
        # elif di
        click.echo('Removing data... ', nl=False)
        pc.delete(path)
        click.echo('Done. \nRemoving search record...', nl=False)
        pc.delete_entry(path, entry_id=entry_id, full_subject=subject)
        click.secho('Done. \n{} has been deleted successfully'.format(path),
                    fg='green')
    except globus_sdk.exc.SearchAPIError as se:
        if se.code == 'NotFound.Generic':
            click.secho('\n{} does not exist, or cannot be found at your '
                        'permission level.'.format(path), fg='yellow')
        else:
            click.secho(str(se))

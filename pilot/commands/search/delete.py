import os
import logging
import click
import globus_sdk
import pilot

log = logging.getLogger(__name__)


@click.command(name='delete', help='Delete file and search record')
@click.argument('path', type=click.Path())
@click.option('--entry-id', default='metadata', help=('Delete a specific entry'
              ' within the search subject, or "null" for a null entry id.'))
@click.option('--subject', default=False, is_flag=True, help=('Delete the'
              ' entire subject comprising all of its associated entry ids'))
@click.option('--dry-run', is_flag=True, default=False,
              help="Show report, but don't actually delete entry/file")
@click.option('--data', 'data_only', is_flag=True,
              help='Delete the data but not the search record', default=False)
@click.option('--metadata', 'metadata_only', default=False, is_flag=True,
              help='Delete the search record but not the data')
# @click.option('--recursive', '-r', default=False, is_flag=True,
#               help='Delete the entire contents of a directory')
def delete_command(path, entry_id, subject, dry_run, data_only,
                   metadata_only):
    pc = pilot.commands.get_pilot_client()
    if not pc.is_logged_in():
        click.echo('You are not logged in.')
        return

    is_dir = False
    path = path.rstrip('/')

    if not metadata_only:
        dir_list = pc.ls(os.path.dirname(path), extended=True)
        basename = os.path.basename(path)
        log.debug('Checking if {} in {}'.format(basename, dir_list.keys()))

        if os.path.basename(path) not in dir_list:
            click.secho('No file "{}" exists'.format(path), fg='yellow')
            return
        elif dir_list[basename]['type'] == 'dir':
            is_dir = True

    sub_url = pc.get_subject_url(path)
    if dry_run:
        click.secho('Dry Run (No Delete Performed)')
        if is_dir:
            click.echo('Deleted directory: {}'.format(path))
        if not metadata_only:
            click.echo('Deleted file: {}'.format(path))
        if not data_only:
            click.echo('Deleted search entry: {}'.format(sub_url))
        return

    try:
        if is_dir:
            entry = pc.get_search_entry(path)
            if entry:
                num_files = len(entry.get('files', []))
                deleted = pc.delete_entry(path)
                pc.delete(path, recursive=True)
                if num_files == deleted:
                    click.echo('Removed {} ({} files)'.format(path, num_files))
                else:
                    click.echo('Removed {} ({}/{} files)'.format(
                        path, deleted, num_files))
                return 0
            subdir_listing = pc.ls(path)
            log.debug('Subdir contains {}'.format(subdir_listing))
            if subdir_listing:
                click.secho('Directory is not empty, contains: {}'
                            ''.format(subdir_listing), fg='yellow')
                return 1
            pc.delete(path, recursive=True)
            click.echo('The Directory {} has been removed'.format(path))
            return
        if not metadata_only:
            click.echo(f'Removing {path}... ')
            pc.delete(path)
        if not data_only:
            click.echo(f'Removing search record {path}...')
            pc.delete_entry(path, entry_id=entry_id, full_subject=subject)
        click.secho('{} has been deleted successfully'.format(path),
                    fg='green')
    except globus_sdk.exc.SearchAPIError as se:
        if se.code == 'NotFound.Generic':
            click.secho('\n{} does not exist, or cannot be found at your '
                        'permission level.'.format(path), fg='yellow')
        else:
            click.secho(str(se))

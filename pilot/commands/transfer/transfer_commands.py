import os
import sys
import json
import logging
import click
import globus_sdk
import datetime
import pilot
import traceback
import contextlib
import pathlib
from pilot.exc import HTTPSClientException, InvalidField, ExitCodes
from pilot.search_parse import get_size
from pilot.commands.endpoint_utils import test_local_endpoint
from jsonschema.exceptions import ValidationError

log = logging.getLogger(__name__)

# Warn people things will take a while when filesize exceeds 1GB
BIG_SIZE_WARNING = 2 ** 30


def load_json(filename):
    if filename is not None and os.path.exists(filename):
        with open(filename) as fh:
            return json.load(fh)
    return {}


@click.command(help='Upload dataframe to location on Globus and categorize it '
                    'in search')
@click.argument('dataframe',
                type=click.Path(exists=True, file_okay=True, dir_okay=True,
                                readable=True, resolve_path=True))
@click.argument('destination', type=click.Path(), required=False)
@click.option('-j', '--json', 'metadata', type=click.Path(),
              help='Add custom metadata. For field reference, go to:\n'
                   'https://github.com/globusonline/pilot1-tools '
                   'and navigate to doc under `docs/reference.rst`')
@click.option('-u', '--update/--no-update', default=False,
              help='Overwrite an existing dataframe and increment the version')
@click.option('--gcp/--no-gcp', default=True,
              help='Use Globus Connect Personal to start a transfer instead '
                   'of uploading using direct HTTP')
@click.option('--dry-run', is_flag=True, default=False,
              help='Do checks and validation but do not upload/ingest. ')
@click.option('--verbose', is_flag=True, default=False)
@click.option('--no-analyze', is_flag=True, default=False,
              help='Analyze the field to collect additional metadata.')
@click.option('--foreign-keys', 'foreign_keys', type=click.Path(),
              help='File containing links to other search records.')
def upload(dataframe, destination, metadata, gcp, update, dry_run,
           verbose, no_analyze, foreign_keys):
    """
    Create a search entry and upload this file to the GCS Endpoint.
    """
    with pilot_code_handler(dataframe, destination, verbose):
        pc = pilot.commands.get_pilot_client()
        transport = 'globus' if gcp else 'http'
        basename = os.path.basename(dataframe)
        click.secho('Uploading {} using {}... '.format(basename,
                                                       transport))
        test_local_endpoint()
        stats = pc.upload(dataframe, destination, metadata=load_json(metadata),
                          globus=gcp, update=update, dry_run=dry_run,
                          skip_analysis=no_analyze,
                          foreign_keys=load_json(foreign_keys))
        short_path = os.path.join(destination, basename)
        if dry_run:
            raise pilot.exc.DryRun(stats=stats, verbose=verbose)
        elif not stats['metadata_modified']:
            raise pilot.exc.NoChangesNeeded(fmt=[short_path])
        click.secho('A transfer has been queued, see `pilot status` for '
                    'an update of the transfer.', fg='green')
        url = pc.get_portal_url(short_path)
        if url:
            click.echo('You can view your new record here: \n{}'.format(url))


@click.command(help='Register an existing dataframe in search', hidden=True)
@click.argument('dataframe',
                type=click.Path(exists=True, file_okay=True, dir_okay=True,
                                readable=True, resolve_path=True),)
@click.argument('destination', type=click.Path(), required=False)
@click.option('-j', '--json', 'metadata', type=click.Path(),
              help='Metadata in JSON format')
@click.option('-u', '--update/--no-update', default=False,
              help='Overwrite an existing dataframe and increment the version')
@click.option('--dry-run', is_flag=True, default=False,
              help='Do checks and validation but do not upload/ingest. ')
@click.option('--verbose', is_flag=True, default=False)
@click.option('--no-analyze', is_flag=True, default=False,
              help='Analyze the field to collect additional metadata.')
@click.option('--foreign-keys', 'foreign_keys', type=click.Path(),
              help='File containing links to other search records.')
def register(dataframe, destination, metadata, update, dry_run, verbose,
             no_analyze, foreign_keys):
    """
    Create a search entry for a pre-existing file
    """
    with pilot_code_handler(dataframe, destination, verbose):
        pc = pilot.commands.get_pilot_client()
        click.secho('Registering {}... '.format(dataframe))
        short_path = os.path.join(destination, os.path.basename(dataframe))
        stats = pc.register(dataframe, destination,
                            metadata=load_json(metadata), update=update,
                            dry_run=dry_run, skip_analysis=no_analyze,
                            foreign_keys=load_json(foreign_keys))
        if dry_run:
            raise pilot.exc.DryRun(stats=stats, verbose=verbose)
        elif not stats['metadata_modified']:
            raise pilot.exc.NoChangesNeeded(fmt=[short_path])
        click.secho('Success!', fg='green')
        url = pc.get_portal_url(short_path)
        if url:
            click.echo('You can view your new record here: \n{}'.format(url))


@contextlib.contextmanager
def pilot_code_handler(dataframe, destination, verbose):
    """
    Handle exceptions for a `pc.register` or `pc.upload` call. If exceptions
    happen, this handler will cleanly catch the exception and print click
    output for the result. Only code exceptions are caught, all other
    exceptions fall through.
    ** parameters **
      ``short_name`` (*string*) the short-hard representation of the relative
      path on the remote endpoint
      ``verbose`` (*bool*) print verbose output
    """
    try:
        pc = pilot.commands.get_pilot_client()
        if not destination:
            dirs = [n for n, d in pc.ls('', extended=True).items()
                    if d['type'] == 'dir']
            raise pilot.exc.NoDestinationProvided(fmt=[dirs])
        yield
    except (ValidationError, InvalidField) as e:
        log.exception(e)
        click.secho('Error Validating Metadata: {}'.format(e), fg='red')
        sys.exit(ExitCodes.INVALID_METADATA)
    except pilot.exc.RecordExists as re:
        last_updated = re.previous_metadata['dc']['dates'][-1]['date']
        dt = datetime.datetime.strptime(last_updated, '%Y-%m-%dT%H:%M:%S.%fZ')
        short_path = os.path.join(destination, os.path.basename(dataframe))
        click.echo('Existing record found for {}, specify -u to update.\n'
                   'Last updated: {: %A, %b %d, %Y}'
                   ''.format(short_path, dt))
        sys.exit(re.CODE)
    except pilot.exc.DryRun as dr:
        pc = pilot.commands.get_pilot_client()
        short_path = os.path.join(destination, os.path.basename(dataframe))
        stats = dr.stats
        stats.update({'subject': pc.get_subject_url(short_path),
                      'url': pc.get_globus_http_url(short_path)})
        click.secho('Success! (Dry Run -- No changes made.)', fg='green')
        click.echo('Pre-existing record: {record_exists}\n'
                   'Files Modified: {files_modified}\n'
                   'Metadata Modified: {metadata_modified}\n'
                   'Version: {version} (Would be updated to {new_version})\n'
                   'Search Subject: {subject}\n'
                   'URL: {url}\n'
                   .format(**stats)
                   )
        if verbose:
            _, metadata = dr.verbose_output
            click.echo(json.dumps(metadata, indent=2))
    except pilot.exc.PilotCodeException as pce:
        if verbose:
            click.echo(pce.verbose_output)
        fg = 'green' if pce.CODE == ExitCodes.SUCCESS else 'yellow'
        click.secho(str(pce), err=True, fg=fg)
        sys.exit(pce.CODE)
    except pilot.exc.AnalysisException as ae:
        click.secho('Error analyzing {}, skipping...'.format(dataframe),
                    fg='yellow')
        if verbose:
            traceback.print_exception(*ae.original_exc_info)
        else:
            click.secho('(Use --verbose to see full error)', fg='yellow')
    except globus_sdk.exc.TransferAPIError as tapie:
        click.secho(tapie.message, fg='yellow')


@click.command(help='Download a file to your local directory.')
@click.argument('path', type=click.Path())
@click.option('--overwrite/--no-overwrite', default=True)
@click.option('--range', help='Download only part of a file. '
                              'Ex: bytes=0-1, 4-5')
def download(path, overwrite, range):
    # TODO -- Downloading single files within mfes is BROKEN! This instead
    # casues all files to be downloaded
    pc = pilot.commands.get_pilot_client()
    fname = os.path.basename(path)
    if os.path.exists(fname) and not overwrite:
        click.echo('Aborted! File {} would be overwritten.'.format(fname))
        return
    try:
        ent = pc.get_search_entry(path, resolve_collections=True,
                                  precise=False)
        if not ent:
            click.secho('No record exists for {}.'.format(path), fg='yellow')
            sys.exit(pilot.exc.ExitCodes.NO_RECORD_EXISTS)
        http_path = pc.get_globus_http_url(path)
        to_download = [f for f in ent['files'] if http_path in f['url']]
        if len(to_download) > 1:
            click.secho('Downloading {} files, totalling {}'.format(
                len(to_download), get_size({'files': to_download})))
        for file_ent in to_download:
            base_path = os.path.dirname(http_path)
            dest = file_ent['url'].replace(base_path, '').lstrip('/')
            if file_ent.get('length') == 0:
                click.secho('{} is an empty file'.format(dest))
                pathlib.Path(dest).touch()
                continue
            r_content = pc.download_parts(file_ent['url'], dest=dest,
                                          project=None, range=range)
            params = {'label': 'Downloading {}'.format(dest),
                      'length': file_ent['length'], 'show_pos': True}
            with click.progressbar(**params) as bar:
                for bytes_written in r_content:
                    bar.update(bytes_written)
    except HTTPSClientException as hce:
        log.exception(hce)
        if hce.http_status == 404:
            click.secho(f'File not found {path}', fg='red')
        else:
            click.secho('An unexpected error occurred, please contact your '
                        'system administrator', fg='red')


@click.command(help='The new path to create')
@click.argument('path', type=click.Path())
def mkdir(path):
    pc = pilot.commands.get_pilot_client()
    if not pc.is_logged_in():
        click.echo('You are not logged in.')
        return
    try:
        pc.mkdir(path)
        click.secho('Created directory {}'.format(path), fg='green')
    except globus_sdk.exc.TransferAPIError as tapie:
        if tapie.code == 'ExternalError.MkdirFailed.Exists':
            click.secho('Directory already exists')
        elif 'No such file or directory' in tapie.message:
            click.secho('Parent directory does not exist', fg='red')
        elif tapie.code == 'EndpointPermissionDenied':
            click.secho('Permission Denied, you do not have access to create '
                        'directories on {}'.format(pc.project.current),
                        fg='red')
        else:
            log.exception(tapie)
            click.secho('Unknown error, please send this to your system '
                        'administrator', fg='red')

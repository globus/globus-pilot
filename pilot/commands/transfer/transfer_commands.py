import os
import sys
import json
import logging
import click
import globus_sdk
import datetime
import pilot
import traceback
from pilot.exc import (RequiredUploadFields, HTTPSClientException,
                       InvalidField, ExitCodes)
from jsonschema.exceptions import ValidationError

log = logging.getLogger(__name__)

# Warn people things will take a while when filesize exceeds 1GB
BIG_SIZE_WARNING = 2 ** 30


@click.command(help='Upload dataframe to location on Globus and categorize it '
                    'in search')
@click.argument('dataframe',
                type=click.Path(exists=True, file_okay=True, dir_okay=False,
                                readable=True, resolve_path=True),)
@click.argument('destination', type=click.Path(), required=False)
@click.option('-j', '--json', 'metadata', type=click.Path(),
              help='Metadata in JSON format')
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
# @click.option('--x-labels', type=click.Path(),
#               help='Path to x label file')
# @click.option('--y-labels', type=click.Path(),
#               help='Path to y label file')
@click.pass_context
def upload(ctx, dataframe, destination, metadata, gcp, update, dry_run,
           verbose, no_analyze):
    """
    Create a search entry and upload this file to the GCS Endpoint.

    # TODO: Fault tolerance for interrupted or failed file uploads (rollback)
    """
    user_metadata = {}
    if metadata is not None:
        with open(metadata) as mf_fh:
            user_metadata = json.load(mf_fh)
    try:
        pc = pilot.commands.get_pilot_client()
        transport = 'globus' if gcp else 'http'
        click.secho('Uploading {} using {}... '.format(dataframe, transport))
        pc.upload(dataframe, destination, metadata=user_metadata, globus=gcp,
                  update=update, dry_run=dry_run, skip_analysis=no_analyze)
        click.secho('Success!', fg='green')
        short_path = os.path.join(destination, os.path.basename(dataframe))
        url = pc.get_portal_url(short_path)
        click.echo('You can view your new record here: \n{}'.format(url))
    except pilot.exc.AnalysisException as ae:
        click.secho('Error analyzing {}, skipping...'.format(dataframe),
                    fg='yellow')
        if verbose:
            traceback.print_exception(*ae.original_exc_info)
        else:
            click.secho('(Use --verbose to see full error)', fg='yellow')
        ctx.invoke(upload, dataframe=dataframe, destination=destination,
                   metadata=metadata, gcp=gcp, update=update, dry_run=dry_run,
                   verbose=verbose, no_analyze=True)
    except (RequiredUploadFields, ValidationError, InvalidField) as e:
        log.exception(e)
        click.secho('Error Validating Metadata: {}'.format(e), fg='red')
        sys.exit(ExitCodes.INVALID_METADATA)
    except pilot.exc.RecordExists as re:
        last_updated = re.previous_metadata['dc']['dates'][-1]['date']
        dt = datetime.datetime.strptime(last_updated, '%Y-%m-%dT%H:%M:%S.%fZ')
        click.echo('Existing record found for {}, specify -u to update.\n'
                   'Last updated: {: %A, %b %d, %Y}'
                   ''.format(os.path.basename(dataframe), dt))
        sys.exit(re.CODE)
    except pilot.exc.PilotCodeException as pce:
        if verbose:
            click.echo(pce.verbose_output)
        fg = 'green' if pce.CODE == ExitCodes.SUCCESS else 'yellow'
        click.secho(str(pce), err=True, fg=fg)
        sys.exit(pce.CODE)


@click.command(help='Register an existing dataframe in search', hidden=True)
@click.argument('dataframe',
                type=click.Path(exists=True, file_okay=True, dir_okay=False,
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
def register(dataframe, destination, metadata, update, dry_run, verbose,
             no_analyze):
    """
    Create a search entry for a pre-existing file
    """
    raise NotImplemented('Refactoring in progress!')


@click.command(help='Download a file to your local directory.')
@click.argument('path', type=click.Path())
@click.option('--overwrite/--no-overwrite', default=True)
@click.option('--range', help='Download only part of a file. '
                              'Ex: bytes=0-1, 4-5')
def download(path, overwrite, range):
    pc = pilot.commands.get_pilot_client()
    fname = os.path.basename(path)
    if os.path.exists(fname) and not overwrite:
        click.echo('Aborted! File {} would be overwritten.'.format(fname))
        return
    try:
        record = pc.get_search_entry(path)
        length = 0
        if record and record.get('files'):
            length = record['files'][0].get('length')
        elif not record:
            click.secho('No record exists for {}, you may want to register it.'
                        .format(path), fg='yellow')
        r_content = pc.download_parts(path, range=range)
        params = {'label': 'Downloading {}'.format(fname), 'length': length,
                  'show_pos': True}
        with click.progressbar(**params) as bar:
            for bytes_written in r_content:
                bar.update(bytes_written)
        click.echo('Saved {}'.format(fname))
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

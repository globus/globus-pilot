import os
import json
import click
import globus_sdk
import datetime
import requests
import pilot
from pilot.search import (scrape_metadata, update_metadata, gen_gmeta,
                          files_modified)
from pilot.exc import RequiredUploadFields
from pilot import transfer_log
from jsonschema.exceptions import ValidationError


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
@click.option('--test', is_flag=True, default=False,
              help='upload/ingest to test locations')
@click.option('--dry-run', is_flag=True, default=False,
              help='Do checks and validation but do not upload/ingest. ')
@click.option('--verbose', is_flag=True, default=False)
@click.option('--no-analyze', is_flag=True, default=False,
              help='Analyze the field to collect additional metadata.')
# @click.option('--x-labels', type=click.Path(),
#               help='Path to x label file')
# @click.option('--y-labels', type=click.Path(),
#               help='Path to y label file')
def upload(dataframe, destination, metadata, gcp, update, test, dry_run,
           verbose, no_analyze):
    """
    Create a search entry and upload this file to the GCS Endpoint.

    # TODO: Fault tolerance for interrupted or failed file uploads (rollback)
    """
    pc = pilot.commands.get_pilot_client()
    if not pc.is_logged_in():
        click.echo('You are not logged in.')
        return

    if test:
        click.secho('Using test location: {}'.format(pc.TESTING_DIR),
                    fg='yellow')
        click.secho('Using test index for Globus Search', fg='yellow')

    if not destination:
        dirs = pc.ls('', test)
        click.echo('No Destination Provided. Please select one from the '
                   'directory:\n{}'.format('\t '.join(dirs)))
        return

    try:
        pc.ls(destination)
    except globus_sdk.exc.TransferAPIError as tapie:
        if tapie.code == 'ClientError.NotFound':
            url = pc.get_globus_app_url('')
            click.secho('Directory does not exist: "{}"\nPlease create it at: '
                        '{}'.format(destination, url), err=True, bg='red')
            return 1
        else:
            click.secho(tapie.message, err=True, bg='red')
            return 1

    if metadata is not None:
        with open(metadata) as mf_fh:
            user_metadata = json.load(mf_fh)
    else:
        user_metadata = {}

    short_path = os.path.join(destination, os.path.basename(dataframe))
    prev_metadata = pc.get_search_entry(short_path)

    url = pc.get_globus_http_url(short_path)
    new_metadata = scrape_metadata(dataframe, no_analyze, pc.profile)

    try:
        new_metadata = update_metadata(new_metadata, prev_metadata,
                                       user_metadata)
        subject = pc.get_subject_url(short_path)
        gmeta = gen_gmeta(subject, pc.get_group(), new_metadata)
    except (RequiredUploadFields, ValidationError) as e:
        click.secho('Error Validating Metadata: {}'.format(e), fg='red')
        return 1

    if json.dumps(new_metadata) == json.dumps(prev_metadata):
        click.secho('Files and search entry are an exact match. No update '
                    'necessary.', fg='green')
        return 1

    if prev_metadata and not update:
        last_updated = prev_metadata['dc']['dates'][-1]['date']
        dt = datetime.datetime.strptime(last_updated, '%Y-%m-%dT%H:%M:%S.%fZ')
        click.echo('Existing record found for {}, specify -u to update.\n'
                   'Last updated: {: %A, %b %d, %Y}'
                   ''.format(short_path, dt))
        return 1

    if dry_run:
        click.echo('Success! (Dry Run -- No changes made.)')
        click.echo('Pre-existing record: {}'.format(
            'yes' if prev_metadata else 'no'))
        click.echo('Version: {}'.format(new_metadata['dc']['version']))
        click.echo('Search Subject: {}\nURL: {}'.format(
            subject, url
        ))
        if verbose:
            click.echo('Ingesting the following data:')
            click.echo(json.dumps(new_metadata, indent=2))
        return

    click.echo('Ingesting record into search...')
    pc.ingest_entry(gmeta, test)
    click.echo('Success!')

    if prev_metadata and not files_modified(new_metadata['files'],
                                            prev_metadata['files']):
        click.echo('Metadata updated, dataframe is already up to date.')
        return
    if gcp:
        local_ep = globus_sdk.LocalGlobusConnectPersonal().endpoint_id
        if not local_ep:
            raise Exception('No local GCP client found')
        auth = pc.get_authorizers()['transfer.api.globus.org']
        tc = globus_sdk.TransferClient(authorizer=auth)
        tdata = globus_sdk.TransferData(
            tc, local_ep, pc.get_endpoint(),
            label='{} Transfer'.format(pc.APP_NAME),
            notify_on_succeeded=False,
            sync_level='checksum',
            encrypt_data=True)
        tdata.add_item(dataframe, pc.get_path(short_path))
        click.echo('Starting Transfer...')
        transfer_result = tc.submit_transfer(tdata)
        tl = transfer_log.TransferLog()
        tl.add_log(transfer_result, short_path)
        click.echo('{}. You can check the status below: \n'
                   'https://app.globus.org/activity/{}/overview\n'
                   'URL will be: {}'.format(
                        transfer_result['message'], transfer_result['task_id'],
                        url)
                   )
    else:
        click.echo('Uploading data...')
        response = pc.upload(short_path)
        if response.status_code == 200:
            click.echo('Upload Successful! URL is \n{}'.format(url))
        else:
            click.echo('Failed with status code: {}'.format(
                response.status_code))


@click.command(help='Download a file to your local directory.')
@click.argument('path', type=click.Path())
@click.option('--test/--no-test', default=False,
              help='download from test location')
@click.option('--overwrite/--no-overwrite', default=True)
@click.option('--range', help='Download only part of a file. '
                              'Ex: bytes=0-1, 4-5')
def download(path, test, overwrite, range):
    pc = pilot.commands.get_pilot_client()
    if not pc.is_logged_in():
        click.echo('You are not logged in.')
        return

    headers = pc.http_headers
    if range:
        try:
            from requests_toolbelt.multipart import decoder
        except ImportError:
            click.secho('"requests-toolbelt" package required for ranges.',
                        bg='red')
            return 255
        headers['Range'] = range

    fname, dirname = os.path.basename(path), os.path.dirname(path)
    if os.path.exists(fname) and not overwrite:
        click.echo('Aborted! File {} would be overwritten.'.format(fname))
        return
    try:
        if not pc.ls(fname, dirname, test):
            click.echo('File "{}" does not exist.'.format(path))
            return 1
        url = pc.get_globus_http_url(fname, dirname, test)
        response = requests.get(url, headers=headers, stream=True)
        with open(fname, 'wb') as fh:
            if range:
                r_content = decoder.MultipartDecoder.from_response(response)
                for part in r_content.parts:
                    fh.write(part.content)
            else:
                # Download content in 1MB chunks
                r_content = response.iter_content(chunk_size=2048)
                lb = 'Downloading {}'.format(fname)
                with click.progressbar(r_content, label=lb,
                                       show_pos=True) as rc:
                    for chunk in rc:
                        fh.write(chunk)

        click.echo('Saved {}'.format(fname))
    except globus_sdk.exc.TransferAPIError:
        click.echo('Directory "{}" does not exist.'.format(dirname))
        return 1

import os
import json
import click
import globus_sdk
import datetime
import requests
import pilot
from pilot.search import scrape_metadata, update_metadata, gen_gmeta


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
@click.option('--test/--no-test', default=True,
              help='upload/ingest to test locations')
@click.option('--dry-run/--no-dry-run', default=False,
              help='Do checks and validation but do not upload/ingest. ')
@click.option('--search-test/--no-search-test', default=True,
              help='Put search data under a special key "testing" to prevent '
                   'test data breaking Globus Search type indexing. This '
                   'prevents needing to reset the index if you decide to '
                   'change the types for your ingested data.')
@click.option('--verbose/--no-verbose', default=False)
# @click.option('--x-labels', type=click.Path(),
#               help='Path to x label file')
# @click.option('--y-labels', type=click.Path(),
#               help='Path to y label file')
def upload(dataframe, destination, metadata, gcp, update, test, dry_run,
           search_test, verbose):
    # pilot upload -j metadata.json <dataframe> <remote rel path>
    # pilot -j metadata.json drug_response.tsv responses
    # check for remote directory
    # check for existing file in remote destination
    #   If file, is update flag set? If yes, get version & bump version
    # Checksum file, get size
    #   If bumping version, check for existing metadata and reuse
    #   Cache existing version and metadata
    #   Update size and checksum, plus any provided metadata
    # Generate GMeta record
    # validate GMeta record
    # Push to Search
    # get task ID
    # PUT dataframe via HTTPS
    # Check status of upload
    # Check status of Search ingest
    # Rollback if failed on either
    # Delete GMetaEntry or dataframe if other fails

    # Handling updates
    # add UUID as id to GMetaEntry
    # move existing dataframe to "jail"
    # delete by ID when update succeeds or fails

    # How to handle state?
    # what if upload is interrupted?
    # Remote log?

    # Check for directory, if so, get list from transfer first
    # Should require login if there are publicly visible records
    pc = pilot.commands.get_pilot_client()
    if not pc.is_logged_in():
        click.echo('You are not logged in.')
        return

    if not destination:
        path = pc.get_path('', '', test)
        dirs = pc.ls('', '', test)
        click.echo('No Destination Provided. Please select one from the '
                   'directory "{}":\n{}'.format(path, '\t '.join(dirs)))
        return

    try:
        pc.ls(dataframe, destination, test)
    except globus_sdk.exc.TransferAPIError:
        url = pc.get_globus_app_url('', test)
        click.echo('Directory does not exist: "{}"\nPlease create it at: {}'
                   ''.format(destination, url), err=True)
        return 1

    if metadata is not None:
        with open(metadata) as mf_fh:
            user_metadata = json.load(mf_fh)
    else:
        user_metadata = {}

    filename = os.path.basename(dataframe)
    prev_metadata = pc.get_search_entry(filename, destination, test)
    if prev_metadata and prev_metadata.get('testing'):
        prev_metadata = prev_metadata['testing']

    url = pc.get_globus_http_url(filename, destination, test)
    new_metadata = scrape_metadata(dataframe, url, 'generic_datatype')
    if prev_metadata and prev_metadata['files'] == new_metadata['files']:
        dataframe_changed = False
    else:
        dataframe_changed = True

    new_metadata = update_metadata(new_metadata, prev_metadata, user_metadata,
                                   files_updated=dataframe_changed)

    if search_test:
        new_metadata = {'testing': new_metadata}
    subject = pc.get_subject_url(filename, destination, test)
    gmeta = gen_gmeta(subject, pc.GROUP, new_metadata)

    if prev_metadata and not update:
        last_updated = prev_metadata['dc']['dates'][-1]['date']
        dt = datetime.datetime.strptime(last_updated, '%Y-%m-%dT%H:%M:%S.%fZ')
        click.echo('Existing record found for {}, specify -u to update.\n'
                   'Last updated: {: %A, %b %d, %Y}'
                   ''.format(filename, dt))
        return 1

    if dry_run:
        click.echo('Success! (Dry Run -- No changes made.)')
        click.echo('Pre-existing record: {}'.format(
            'yes' if prev_metadata else 'no'))
        if search_test:
            version = new_metadata['testing']['dc']['version']
        else:
            version = new_metadata['dc']['version']
        click.echo('Version: {}'.format(version))
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
    if not dataframe_changed:
        click.echo('Metadata updated, dataframe is already up to date.')
        return
    if gcp:
        local_ep = globus_sdk.LocalGlobusConnectPersonal().endpoint_id
        if not local_ep:
            raise Exception('No local GCP client found')
        auth = pc.get_authorizers()['transfer.api.globus.org']
        tc = globus_sdk.TransferClient(authorizer=auth)
        tdata = globus_sdk.TransferData(
            tc, local_ep, pc.ENDPOINT,
            label='{} Transfer'.format(pc.APP_NAME),
            sync_level='checksum')
        tdata.add_item(dataframe, pc.get_path(filename, destination, test))
        click.echo('Starting Transfer...')
        transfer_result = tc.submit_transfer(tdata)
        click.echo('{}. You can check the status below: \n'
                   'https://app.globus.org/activity/{}/overview\n'
                   'URL will be: {}'.format(
                        transfer_result['message'], transfer_result['task_id'],
                        url)
                   )
    else:
        click.echo('Uploading data...')
        response = pc.upload(dataframe, destination, test)
        if response.status_code == 200:
            click.echo('Upload Successful! URL is \n{}'.format(url))
        else:
            click.echo('Failed with status code: {}'.format(
                response.status_code))


@click.command()
@click.argument('dataframe', type=click.Path())
@click.argument('destination', type=click.Path(), required=False)
@click.option('--test/--no-test', default=True,
              help='download from test location')
@click.option('--overwrite', is_flag=True, default=False)
def download(dataframe, destination, test, overwrite):
    pc = pilot.commands.get_pilot_client()
    if not pc.is_logged_in():
        click.echo('You are not logged in.')
        return

    filename = os.path.basename(dataframe)
    if os.path.exists(filename) and not overwrite:
        click.echo('Aborted! File {} would be overwritten.'.format(filename))
        return
    try:
        if not pc.ls(filename, destination, test):
            click.echo('File "{}" does not exist.'.format(filename))
            return 1
        url = pc.get_globus_http_url(filename, destination, test)
        response = requests.get(url, headers=pc.http_headers, stream=True)
        with open(filename, 'wb') as fh:
            for chunk in response.iter_content(chunk_size=2048):
                fh.write(chunk)
        click.echo('Saved {}'.format(filename))
    except globus_sdk.exc.TransferAPIError:
        click.echo('Directory "{}" does not exist.'.format(destination))
        return 1

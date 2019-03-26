import os
import json
import click
import globus_sdk
from pilot.client import PilotClient
from pilot.search import gen_remote_file_manifest, gen_gmeta

@click.command(help='Upload dataframe to location on Globus and categorize it '
                    'in search. \n\nCommand still in development! Destination '
                    'upload and search indexing limited to testing locations.')
@click.argument('dataframe',
                type=click.Path(exists=True, file_okay=True, dir_okay=False,
                                readable=True, resolve_path=True),
                )
@click.argument('destination', type=click.Path())
@click.option('-j', '--json', 'metadata', type=click.Path(),
              help='Metadata in JSON format')
@click.option('-u', '--update/--no-update', default=False,
              help='Overwrite an existing dataframe and increment the version')
# @click.option('--validate-only', is_flag=True,
#               help='Don\'t actually create record and upload file, test only')
# @click.option('--x-labels', type=click.Path(),
#               help='Path to x label file')
# @click.option('--y-labels', type=click.Path(),
#               help='Path to y label file')
def upload(dataframe, destination, metadata, update):
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
    pc = PilotClient()
    if not pc.is_logged_in():
        click.echo('You are not logged in.')
        return

    if metadata is not None:
        with open(metadata) as mf_fh:
            metadata_content = json.load(mf_fh)
    else:
        metadata_content = None
    filename = os.path.basename(dataframe)

    current_record = pc.get_search_entry(filename, destination, testing=True)

    url = pc.get_dataframe_url(filename, destination, testing=True)
    rfm = gen_remote_file_manifest(dataframe, url)
    data = {'testing': {'remote_file_manifest': rfm,
                        'dc': metadata_content}}
    subject = pc.get_subject(filename, destination, testing=True)

    if current_record:
        if update:
            from pprint import pprint
            pprint(current_record)
            version = int(current_record['testing']['dc']['version'])
            if data:
                current_record.update(data)
            current_record['testing']['dc']['version'] = version + 1
            gmeta = gen_gmeta(subject, pc.GROUP, data)
        else:
            click.echo('Existing record found for {}, specify -u to update.'
                       ''.format(filename))
            return
    else:
        gmeta = gen_gmeta(subject, pc.GROUP, data)

    #@hack require version
    try:
        from pprint import pprint
        pprint(gmeta)
        gmeta['ingest_data']['gmeta'][0]['content']['testing']['dc']['version']
    except:
        raise ValueError('Metadata json must be supplied with a version: Ex.'
                         '{"version": 1}')

    click.echo('Ingesting record into search...')
    pc.ingest_entry(gmeta, testing=True)
    click.echo('Success!')
    click.echo('Uploading data...')
    status_code = pc.upload(dataframe, destination, testing=True)
    if status_code == 200:
        click.echo('Upload Successful! URL is now {}'.format(url))
    else:
        click.echo('Failed with status code: ' + status_code)

@click.command()
def download():
    click.echo('download command')

    vegas_climate_csv = requests.get('https://a4969.36fe.dn.glob.us/portal/catalog/dataset_las/1952.csv').text
    

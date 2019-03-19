import click

@click.command()
@click.argument('dataframe', type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True))
@click.argument('destination', type=click.Path())
@click.option('-j', '--json', 'string',
              help='Metadata in JSON format')
@click.option('-u', '--update', is_flag=True,
              help='Overwrite an existing dataframe and increment the version')
@click.option('--validate-only', is_flag=True,
              help='Don\'t actually create record and upload file, test only')
@click.option('--x-labels', type=click.Path(),
              help='Path to x label file')
@click.option('--y-labels', type=click.Path(),
              help='Path to y label file')
def upload():
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
    

    click.echo('upload command')
    # Check for directory, if so, get list from transfer first
    # Should require login if there are publicly visible records
    pc = PilotClient()
    if not pc.is_logged_in():
        click.echo('You are not logged in.')
        return
    else:
        search_authorizer = pc.get_authorizers()['search.api.globus.org']
        sc = globus_sdk.SearchClient(authorizer=search_authorizer)
        
    client = NativeClient(client_id=CLIENT_ID, app_name=APP_NAME)
    client.login(requested_scopes=SCOPES)

    tokens = client.load_tokens(requested_scopes=SCOPES)
    auther = globus_sdk.AccessTokenAuthorizer(
        tokens['search.api.globus.org']['access_token'])
    sc = globus_sdk.SearchClient(authorizer=auther)

    preview = ingest_doc['ingest_data']['subject']
    print(preview)
    print('Ingest these to "{}"?'.format(
        sc.get_index(INDEX).data['display_name']))
    #user_input = input('Y/N> ')
    #if user_input in ['yes', 'Y', 'y', 'yarr']:
    result = sc.ingest(INDEX, ingest_doc)
    print('Finished')
    print(result)

    # Autoactivate the endpoint
    resp = requests.post(base_url + '/endpoint/' + endpoint_uuid + '/autoactivate',
                        headers=headers)
    print(resp.status_code)
    print(resp.text)
    
    # Create the header
    headers = {'Authorization':'Bearer '+ tokens['tokens']['petrel_https_server']['access_token']}

    # Pass the file pointer reference to the requests library for the PUT
    image_data = open('vegas.png', 'rb')

    # Get the user info as JSON
    resp = requests.put('https://testbed.petrel.host/test/jhtutorial/users/' + username + '/vegas.png',
                    headers=headers, data=image_data, allow_redirects=False)
    print(resp.status_code)

@click.command()
def download():
    click.echo('download command')

    vegas_climate_csv = requests.get('https://a4969.36fe.dn.glob.us/portal/catalog/dataset_las/1952.csv').text
    

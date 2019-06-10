#!/usr/bin/env python
"""
Helper script to ingest generated data to a search index.

You must have access to a search index for this to work.

"""
import sys
import pprint
import json
import globus_sdk
from fair_research_login import NativeClient

SCOPES = ['urn:globus:auth:scope:search.api.globus.org:all']
CLIENT_ID = 'e4d82438-00df-4dbd-ab90-b6258933c335'
INDEX = '889729e8-d101-417d-9817-fa9d964fdbc9'

APP_NAME = 'Pilot 1 Ingest'

def  get_size(size):
    #2**10 = 1024
    power = 2**10
    n = 0
    Dic_powerN = {0 : '', 1: 'k', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /=  power
        n += 1
    return size, Dic_powerN[n]+'B'

def ingest(filename):

    with open(filename) as f:
        ingest_doc = json.loads(f.read())

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

def listind():
    client = NativeClient(client_id=CLIENT_ID, app_name=APP_NAME)
    client.login(requested_scopes=SCOPES)

    tokens = client.load_tokens(requested_scopes=SCOPES)
    auther = globus_sdk.AccessTokenAuthorizer(
        tokens['search.api.globus.org']['access_token'])
    sc = globus_sdk.SearchClient(authorizer=auther)

    search_results = sc.search(index_id=INDEX, q='*', limit=10000)

    header = 'Title                Data       Dataframe Rows   Cols   Size   Filename'
    print(header)
    for i in search_results['gmeta']:
        j = i['content'][0]
        pprint.pprint(j)
        s, h = get_size(j['files'][0]['length'])
        size = str(int(s)) + ' ' + h
        print(
            '{:21.20}'.format(j['dc']['titles'][0]['title']) +
            '{:11.10}'.format(j['ncipilot']['data_type']) +
            '{:10.9}'.format(j['ncipilot']['dataframe_type']) +
             '{:7.6}'.format(str(j['field_metadata']['numrows'])) +
             '{:7.6}'.format(str(j['field_metadata']['numcols'])) +
            '{:7.6}'.format(size) +
            '{:.16}'.format(j['files'][0]['filename'])
            )

def dump():
    client = NativeClient(client_id=CLIENT_ID, app_name=APP_NAME)
    client.login(requested_scopes=SCOPES)

    tokens = client.load_tokens(requested_scopes=SCOPES)
    auther = globus_sdk.AccessTokenAuthorizer(
        tokens['search.api.globus.org']['access_token'])
    sc = globus_sdk.SearchClient(authorizer=auther)

    search_results = sc.search(index_id=INDEX, q='*', limit=10000)

    for i in search_results['gmeta']:
        # print(i['subject'])
        # print(i['subject'].lstrip('globus://ebf55996-33bf-11e9-9fa4-0a06afd4a22e/').replace('/','-'))
        fname  = i['subject'].lstrip('globus://ebf55996-33bf-11e9-9fa4-0a06afd4a22e/').replace('/','-') + '.gmeta'
        with open(fname, 'w') as f:
            f.write(json.dumps(i))      
            
def delete(filename):

    with open(filename) as f:
        ingest_doc = json.loads(f.read())

    client = NativeClient(client_id=CLIENT_ID, app_name=APP_NAME)
    client.login(requested_scopes=SCOPES)

    tokens = client.load_tokens(requested_scopes=SCOPES)
    auther = globus_sdk.AccessTokenAuthorizer(
        tokens['search.api.globus.org']['access_token'])
    sc = globus_sdk.SearchClient(authorizer=auther)

    subject = ingest_doc['ingest_data']['subject']
    print(subject)
    print('Deleting from "{}"?'.format(
        sc.get_index(INDEX).data['display_name']))
    #user_input = input('Y/N> ')
    #if user_input in ['yes', 'Y', 'y', 'yarr']:
    result = sc.delete_subject(INDEX, subject)
    print('Finished')
    print(result)

def tasks():

    client = NativeClient(client_id=CLIENT_ID, app_name=APP_NAME)
    client.login(requested_scopes=SCOPES)

    tokens = client.load_tokens(requested_scopes=SCOPES)
    auther = globus_sdk.AccessTokenAuthorizer(
        tokens['search.api.globus.org']['access_token'])
    sc = globus_sdk.SearchClient(authorizer=auther)
    print(sc.get_task_list(INDEX))
    print('Finished')

        
if __name__ == '__main__':
    if sys.argv[1] == 'i':
        filename = sys.argv[2]
        ingest(filename)
    elif sys.argv[1] == 'd':
        filename = sys.argv[2]
        delete(filename)
    elif sys.argv[1] == 'dump':
        dump()
    elif sys.argv[1] == 't':
        tasks()
    elif sys.argv[1] == 'l':
        listind()
    else:
        print('Command not recognized')

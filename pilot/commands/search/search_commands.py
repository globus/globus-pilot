import click
import globus_sdk
from pilot.client import PilotClient
from pilot.config import config

def  get_size(size):
    #2**10 = 1024
    power = 2**10
    n = 0
    Dic_powerN = {0 : '', 1: 'k', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /=  power
        n += 1
    return size, Dic_powerN[n]+'B'

@click.command()
def list():
    # Should require login if there are publicly visible records
    pc = PilotClient()
    if not pc.is_logged_in():
        click.echo('You are not logged in.')
        return
    else:
        search_authorizer = pc.get_authorizers()['search.api.globus.org']
        sc = globus_sdk.SearchClient(authorizer=search_authorizer)
        # TO DO: iterate instead of upping limit
        search_results = sc.search(index_id=pc.SEARCH_INDEX, q='*', limit=100)

        header = 'Title                Data       Dataframe Rows   Cols   Size   Filename'
        print(header)
        for i in search_results['gmeta']:
            j = i['content'][0]
            s, h = get_size(j['remote_file_manifest']['length'])
            size = str(int(s)) + ' ' + h
            print(
                '{:21.20}'.format(j['dc']['titles'][0]['title']) +
                '{:11.10}'.format(j['ncipilot']['data_type']) +
                '{:10.9}'.format(j['ncipilot']['dataframe_type']) +
                '{:7.6}'.format(str(j['ncipilot']['numrows'])) +
                '{:7.6}'.format(str(j['ncipilot']['numcols'])) +
                '{:7.6}'.format(size) +
                '{:.16}'.format(j['remote_file_manifest']['filename'])
                )

@click.command()
def describe():
    click.echo('describe command')


@click.command()
def validate():
    click.echo('validate command')


@click.command()
def stage():
    click.echo('list command')

import os
import click
import globus_sdk
import urllib
import datetime
from pilot.client import PilotClient


def get_size(result):
    size = result['remote_file_manifest']['length']
    # 2**10 = 1024
    power = 2**10
    n = 0
    Dic_powerN = {0: '', 1: 'k', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1

    return '{} {}'.format(int(size), Dic_powerN[n])


def get_identifier(result):
    if result.get('remote_file_manifest'):
        rfm_url = result['remote_file_manifest']['url']
    else:
        rfm_url = result['files'][0]['url']
    url = urllib.parse.urlsplit(rfm_url)
    identifier = url.path.replace(PilotClient.TESTING_DIR + '/', '')
    identifier = identifier.replace(PilotClient.BASE_DIR + '/', '')
    return identifier


@click.command(name='list', help='List known records in Globus Search')
@click.option('--test/--no-test', default=False)
def list_command(test):
    # Should require login if there are publicly visible records
    pc = PilotClient()
    if not pc.is_logged_in():
        click.echo('You are not logged in.')
        return

    search_authorizer = pc.get_authorizers()['search.api.globus.org']
    sc = globus_sdk.SearchClient(authorizer=search_authorizer)
    # TO DO: iterate instead of upping limit
    search_results = sc.search(index_id=pc.get_index(test), q='*', limit=100)

    fmt = '{:21.20}{:11.10}{:10.9}{:7.6}{:7.6}{:7.6}{}'
    columns = [
        ('Title', lambda r: r['dc']['titles'][0]['title']),
        ('Data', lambda r: r['ncipilot']['data_type']),
        ('Dataframe', lambda r: r['ncipilot']['dataframe_type']),
        ('Rows', lambda r: str(r['ncipilot']['numrows'])),
        ('Cols', lambda r: str(r['ncipilot']['numcols'])),
        ('Size', get_size),
        ('Filename', get_identifier),
    ]

    # Build row data
    rows = []
    for result in search_results['gmeta']:
        content = result['content'][0]
        if content.get('testing'):
            content = content['testing']
        row = []
        for _, function in columns:
            try:
                row.append(function(content))
            except Exception:
                row.append('')
                # raise
        rows.append(row)

    formatted_rows = [fmt.format(*r) for r in rows]
    header = fmt.format(*[c[0] for c in columns])
    output = '{}\n{}'.format(header, '\n'.join(formatted_rows))
    click.echo_via_pager(output)


def get_dates(result):
    dates = result['dc']['dates']
    fdates = []
    for date in dates:
        dt = datetime.datetime.strptime(date['date'], '%Y-%m-%dT%H:%M:%S.%fZ')
        fdates.append('{}: {: %A, %b %d, %Y}'.format(date['dateType'], dt))
    return fdates


@click.command(help='Output info about a dataset')
@click.argument('path', type=click.Path())
@click.option('--test/--no-test', default=False)
def describe(path, test):
    pc = PilotClient()
    if not pc.is_logged_in():
        click.echo('You are not logged in.')
        return

    fname, dirname = os.path.basename(path), os.path.dirname(path)
    entry = pc.get_search_entry(fname, dirname, test)
    if not entry:
        entry = pc.get_search_entry(fname, dirname, old=True)

    if not entry:
        click.echo('Unable to find entry')
        return

    if entry.get('testing'):
        entry = entry['testing']

    fmt = '{:21.20}{}'
    columns = [
        ('Title', lambda r: r['dc']['titles'][0]['title']),
        ('Authors', lambda r: [c['creatorName'] for c in r['dc']['creators']]),
        ('Publisher', lambda r: r['dc']['publisher']),
        ('Subjects', lambda r: [s['subject'] for s in r['dc']['subjects']]),
        ('Dates', get_dates),
        ('Data', lambda r: r['ncipilot']['data_type']),
        ('Dataframe', lambda r: r['ncipilot']['dataframe_type']),
        ('Rows', lambda r: str(r['ncipilot']['numrows'])),
        ('Columns', lambda r: str(r['ncipilot']['numcols'])),
        ('Formats', lambda r: r['dc']['formats']),
        ('Version', lambda r: r['dc']['version']),
        ('Size', get_size),
        ('Filename', get_identifier),
        ('Description', lambda r: r['dc']['descriptions'][0]['description']),
    ]

    formatted_rows = []
    for name, func in columns:
        try:
            content = func(entry)
        except Exception:
            content = ''
            # raise
        if content and isinstance(content, list):
            formatted_rows.append(fmt.format(name, content[0]))
            extended = [fmt.format('', item) for item in content[1:]]
            formatted_rows += extended
        else:
            formatted_rows.append(fmt.format(name, content))

    output = '\n'.join(formatted_rows)
    click.echo(output)

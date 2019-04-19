import os
import urllib
import json
import datetime
import click
import globus_sdk
from pilot.client import PilotClient

PORTAL_DETAIL_PAGE_PREFIX = 'https://petreldata.net/nci-pilot1/detail/'


def get_single_file_rfm(result):
    """
    The location has changed over time, it may be in a couple different
    locations. This function guarantees to fetch from the correct one.
    """
    if result.get('remote_file_manifest'):
        return result['remote_file_manifest']
    elif result.get('files'):
        return result['files'][0]


def get_size(result):
    size = get_single_file_rfm(result)['length']
    # 2**10 = 1024
    power = 2**10
    n = 0
    Dic_powerN = {0: '', 1: 'k', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1

    return '{} {}'.format(int(size), Dic_powerN[n])


def get_identifier(result):
    rfm_url = get_single_file_rfm(result)['url']
    url = urllib.parse.urlsplit(rfm_url)
    identifier = url.path.replace(PilotClient.TESTING_DIR + '/', '')
    identifier = identifier.replace(PilotClient.BASE_DIR + '/', '')
    return identifier


def fetch_format(columns, search_entry, fmt_func, list_fmt_func):
    """
    Fetch data in your defined 'columns', for a given Globus Search entry.
    fmt_func is a function that formats simple types, while
    list_fmt_func is a function that formats lists
    """
    formatted_rows = []

    for name, func in columns:
        try:
            content = func(search_entry)
        except Exception:
            content = ''
            # raise
        if content and isinstance(content, list):
            formatted_rows += list_fmt_func(name, content)
        else:
            formatted_rows += fmt_func(name, content)
    return '\n'.join(formatted_rows)


@click.command(name='list', help='List known records in Globus Search')
@click.option('--test/--no-test', default=False,
              help='Look for entry on test index/endpoint path.')
@click.option('--json/--no-json', 'output_json', default=False,
              help='Output as JSON.')
@click.option('--limit', type=int, default=100,
              help='Limit returned results to the number provided')
def list_command(test, output_json, limit):
    # Should require login if there are publicly visible records
    pc = PilotClient()
    if not pc.is_logged_in():
        click.echo('You are not logged in.')
        return

    search_authorizer = pc.get_authorizers()['search.api.globus.org']
    sc = globus_sdk.SearchClient(authorizer=search_authorizer)
    # TO DO: iterate instead of upping limit
    search_results = sc.search(index_id=pc.get_index(test), q='*', limit=limit)

    if output_json:
        click.echo(json.dumps(search_results.data, indent=4))
        return

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
@click.option('--test/--no-test', default=False,
              help='Look for entry on test index/endpoint path.')
@click.option('--json/--no-json', 'output_json', default=False,
              help='Output as JSON.')
def describe(path, test, output_json):
    pc = PilotClient()
    if not pc.is_logged_in():
        click.echo('You are not logged in.')
        return

    old_entry = False
    fname, dirname = os.path.basename(path), os.path.dirname(path)
    entry = pc.get_search_entry(fname, dirname, test)
    if not entry:
        old_entry = True
        entry = pc.get_search_entry(fname, dirname, old=True)

    if not entry:
        click.echo('Unable to find entry')
        return

    if output_json:
        click.echo(json.dumps(entry, indent=4))
        return

    general_fmt = '{:21.20}{}'
    general_columns = [
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

    def format_list(name, content):
        return [general_fmt.format(name, content[0])] + \
               [general_fmt.format('', item) for item in content[1:]]

    def format_entry(name, content):
        return [general_fmt.format(name, content)]

    output = fetch_format(general_columns, entry, format_entry, format_list)

    fmt = ('{:21.20}{:7.6}{:7.6}{:7.6}{:7.6}'
           '{:12.11}{:7.6}{:8.7}{:7.6}{:7.6}'
           '{:7.6}{:7.6}{:9.8}'
           )
    field_metadata = [
        ('Column Name', 'name'),
        ('25-PCTL', '25'),
        ('50-PCTL', '50'),
        ('75-PCTL', '75'),
        ('Count', 'count'),

        ('Top Repeat', 'top'),
        ('Unique', 'unique'),
        ('Format', 'format'),
        ('Min', 'min'),
        ('Max', 'max'),

        ('Mean', 'mean'),
        ('Std', 'std'),
        ('Type', 'type'),
    ]
    names = [n for n, f in field_metadata]
    keys = [f for n, f in field_metadata]
    fm_output = []
    try:
        for field in entry['field_metadata']['field_definitions']:
            f_metadata = [str(field.get(key, '')) for key in keys]
            fm_output.append(fmt.format(*f_metadata))

        field_metadata_names = fmt.format(*names)
        output = '{}\n\nField Metadata\n{}\n{}'.format(output,
                                                       field_metadata_names,
                                                       '\n'.join(fm_output))
    except KeyError:
        output = '{}\n\nField Metadata\nNo Field Metadata'.format(output)

    if not test:
        sub = pc.get_subject_url(fname, dirname, test, old=old_entry)
        qsub = urllib.parse.quote_plus(urllib.parse.quote_plus(sub))
        portal_url = '{}{}'.format(PORTAL_DETAIL_PAGE_PREFIX, qsub)
        other_data = [general_fmt.format('Subject', sub),
                      general_fmt.format('Portal URL', portal_url)]
        output = '{}\n\nOther Data\n{}'.format(output, '\n'.join(other_data))

    click.echo(output)

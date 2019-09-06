import urllib
import json
import logging
import click
from pilot import commands
from pilot.search_parse import (
    parse_result, get_titles, get_field_metadata, get_field_metadata_titles
)

log = logging.getLogger(__name__)


def get_short_path(result):
    pc = commands.get_pilot_client()
    base_path = pc.get_path('')
    sub = urllib.parse.urlparse(result['subject'])
    return sub.path.replace(base_path, '').lstrip('/')


def search_by_project(project=None, custom_params=None):
    pc = commands.get_pilot_client()
    search_data = {
        'q': '*',
        'filters': {
            'field_name': 'project_metadata.project-slug',
            'type': 'match_all',
            'values': [project or pc.project.current]
        }
    }
    custom_params = custom_params or {}
    search_data.update(custom_params)
    sc = pc.get_search_client()
    return sc.post_search(pc.get_index(project=project), search_data).data


@click.command(name='list', help='List known records in Globus Search')
@click.option('--json/--no-json', 'output_json', default=False,
              help='Output as JSON.')
@click.option('--limit', type=int, default=100,
              help='Limit returned results to the number provided')
def list_command(output_json, limit):
    # Should require login if there are publicly visible records
    pc = commands.get_pilot_client()
    if not pc.is_logged_in():
        click.echo('You are not logged in.')
        return

    search_results = search_by_project()
    if output_json:
        click.echo(json.dumps(search_results.data, indent=4))
        return

    items = ['title', 'data', 'dataframe', 'rows', 'columns', 'size']
    titles = get_titles(items) + ['Path']
    fmt = '{:21.20}{:11.10}{:10.9}{:7.6}{:7.6}{:7.6}{}'
    output = [fmt.format(*titles)]
    for result in search_results['gmeta']:
        # If this path refers to a result in a different base location, skip
        # it, it isn't part of this project
        if pc.get_path('') not in result['subject']:
            continue

        data = dict(parse_result(result['content'][0]))
        parsed = [data.get(name) for name in items] + [get_short_path(result)]
        parsed = [str(p) for p in parsed]

        output.append(fmt.format(*parsed))
    click.echo('\n'.join(output))


@click.command(help='Output info about a dataset')
@click.argument('path', type=click.Path())
@click.option('--json/--no-json', 'output_json', default=False,
              help='Output as JSON.')
def describe(path, output_json):
    pc = commands.get_pilot_client()
    if not pc.is_logged_in():
        click.echo('You are not logged in.')
        return

    entry = pc.get_search_entry(path)

    if not entry:
        click.echo('Unable to find entry')
        return

    if output_json:
        click.echo(json.dumps(entry, indent=4))
        return

    # lines of output which will be printed to console
    output = []

    # print general data
    general_fmt = '{:21.20}{}'
    general_columns = ['title', 'authors', 'publisher', 'subjects', 'dates',
                       'data', 'dataframe', 'rows', 'columns', 'formats',
                       'version', 'size', 'description']
    raw_data = dict(parse_result(entry))

    tdata = zip(get_titles(general_columns),
                [raw_data[name] for name in general_columns])
    for title, data in tdata:
        if isinstance(data, list):
            output += [general_fmt.format(title, line) for line in data[:1]]
            output += [general_fmt.format('', line) for line in data[1:]]
        else:
            output.append(general_fmt.format(title, data))
    output += ['', '']

    # print field metadata
    fmt = ('{:21.20}'
           '{:8.7}{:7.6}{:5.4}{:12.11}{:7.6}'
           '{:7.6}{:7.6}{:7.6}{:7.6}'
           '{:8.7}{:8.7}{:8.7}'
           )
    output.append(fmt.format(*get_field_metadata_titles()))
    for entry in get_field_metadata(entry):
        fm_names, fm_data = zip(*entry)
        output.append(fmt.format(*[str(i) for i in fm_data]))

    # print other useful data
    other_data = [general_fmt.format('Subject', pc.get_subject_url(path)),
                  general_fmt.format('Portal', pc.get_portal_url(path))]
    output = '\n'.join(output)
    output = '{}\n\nOther Data\n{}'.format(output, '\n'.join(other_data))
    click.echo(output)

import os
import urllib
import json
import logging
import click
from pilot import commands
from pilot.search_parse import (
    parse_result, get_titles, get_common_path, get_relative_paths,
    get_formatted_field_metadata, get_formatted_fields
)
from pilot.search_discovery import get_matching_file

log = logging.getLogger(__name__)


def get_short_path(result):
    pc = commands.get_pilot_client()
    base_path = pc.get_path('')
    sub = urllib.parse.urlparse(result['subject'])
    return sub.path.replace(base_path, '').lstrip('/')


def get_location_info(short_path):
    pc = commands.get_pilot_client()
    return ['Location Information',
            '{:21.20}{}'.format('Subject', pc.get_subject_url(short_path)),
            '{:21.20}{}'.format('Portal', pc.get_portal_url(short_path))]


@click.command(name='list', help='List known records in Globus Search')
@click.option('--json/--no-json', 'output_json', default=False,
              help='Output as JSON.')
@click.option('--limit', type=int, default=100,
              help='Limit returned results to the number provided')
def list_command(output_json, limit):
    # Should require login if there are publicly visible records
    pc = commands.get_pilot_client()
    project = pc.project.current
    search_results = pc.search(project=project, custom_params={'limit': limit})
    if output_json:
        click.echo(json.dumps(search_results, indent=4))
        return

    results = 'Showing {}/{} of total results for "{}"'.format(
        search_results['count'], search_results['total'], project)
    items = ['title', 'data', 'dataframe', 'rows', 'columns', 'size']
    titles = get_titles(items) + ['Path']
    fmt = '{:21.20}{:11.10}{:10.9}{:7.6}{:7.6}{:7.6}{}'
    output = [results, fmt.format(*titles)]
    for result in search_results['gmeta']:
        # If this path refers to a result in a different base location, skip
        # it, it isn't part of this project
        if pc.get_path('') not in result['subject']:
            log.debug('Skipping result {}'.format(result['subject']))
            continue

        data = dict(parse_result(result['content'][0], items))
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
    entry = pc.get_search_entry(path)
    if not entry:
        click.echo('Unable to find entry')
        return

    if output_json:
        click.echo(json.dumps(entry, indent=4))
        return

    single_file_entry = get_matching_file(pc.get_globus_http_url(path), entry)

    if single_file_entry:
        cols = ['title', 'authors', 'publisher', 'subjects', 'dates',
                'data', 'dataframe', 'rows', 'columns',
                'formats', 'version', 'size', 'description']
        output = '\n'.join(
            get_formatted_fields(entry, cols) +
            [''] +
            get_formatted_field_metadata(entry, single_file_entry.get('url')) +
            ['', ''] +
            get_location_info(path)
        )
    else:
        cols = ['title', 'authors', 'publisher', 'subjects', 'dates',
                'formats', 'version', 'combined_size', 'description',
                'files']
        output = '\n'.join(
            get_formatted_fields(entry, cols) +
            [''] +
            get_location_info(path)
        )

    click.echo(output)

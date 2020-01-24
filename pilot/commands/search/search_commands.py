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
    sub = urllib.parse.urlparse(result['subject'])
    return sub.path.replace(pc.get_path(''), '').lstrip('/')


def get_relative_path_from_entries(entry, file_info):
    relative_path = ''
    for path in get_relative_paths(entry):
        if path in file_info['url']:
            relative_path = path
            break
    return relative_path


def get_single_file_info(entry, file_info):
    rp = get_relative_path_from_entries(entry, file_info)
    name = rp or file_info.get('filename', '')
    mimetype = file_info.get('mime_type', '')
    field_metadata = file_info.get('field_metadata')
    info = []
    if not field_metadata:
        return []
    elif isinstance(field_metadata, list):
        for store in field_metadata:
            keystore = store.get('store_key', '')
            info += (
                ['{} ({}) Keystore: {}'.format(name, mimetype, keystore)] +
                get_formatted_field_metadata(store) +
                ['']
            )
    else:
        info = (
            ['{} ({})'.format(name, mimetype)] +
            get_formatted_field_metadata(field_metadata) +
            ['']
        )
    return info


def get_location_info(entry):
    short_path = os.path.basename(get_common_path(entry))
    pc = commands.get_pilot_client()
    return ['Location Information',
            '{:21.20}{}'.format('Subject', pc.get_subject_url(short_path)),
            '{:21.20}{}'.format('Portal', pc.get_portal_url(short_path))]


@click.command(name='list', help='List known records in Globus Search')
@click.argument('path', type=click.Path(), required=False, default='')
@click.option('--json/--no-json', 'output_json', default=False,
              help='Output as JSON.')
@click.option('--limit', type=int, default=100,
              help='Limit returned results to the number provided')
@click.option('--relative/--no-relative', default=True,
              help='Only list results relative to project')
@click.option('--all', 'all_recs', default=False, is_flag=True,
              help='Do not filter on project')
def list_command(path, output_json, limit, relative, all_recs):
    # Should require login if there are publicly visible records
    pc = commands.get_pilot_client()
    project = pc.project.current
    search_params = {'limit': limit}
    if all_recs:
        search_params['filters'], relative = [], False
    search_results = pc.search(project=project, custom_params=search_params)
    log.debug(search_results)
    if output_json:
        click.echo(json.dumps(search_results, indent=4))
        return
    path_sub = pc.get_subject_url(path) if relative else path
    curated_results = [r for r in search_results['gmeta']
                       if path_sub in r['subject']]

    results = 'Showing {}/{} of total results for "{}"'.format(
        len(curated_results), search_results['total'], project)
    items = ['title', 'data', 'dataframe', 'rows', 'columns', 'size']
    titles = get_titles(items) + ['Path']
    fmt = '{:21.20}{:11.10}{:10.9}{:7.6}{:7.6}{:7.6}{}'
    output = []
    for result in curated_results:
        # If this path refers to a result in a different base location, skip
        # it, it isn't part of this project
        if relative and pc.get_path('') not in result['subject']:
            log.debug('Skipping result {}'.format(result['subject']))
            continue

        data = dict(parse_result(result['content'][0], items))
        parsed = [data.get(name) for name in items]
        parsed += [get_short_path(result) if relative else result['subject']]
        parsed = [str(p) for p in parsed]

        output.append(fmt.format(*parsed))
    if not output:
        click.secho('No results to display for "{}"'.format(path or '/'),
                    fg='yellow')
    else:
        output = [results, fmt.format(*titles)] + output
        click.echo('\n'.join(output))

    result_names = [os.path.basename(r['subject']) for r in curated_results]
    path_info = pc.ls(path, extended=True)
    dirs = [name for name, info in path_info.items()
            if info['type'] == 'dir' and name not in result_names]
    if dirs:
        click.echo('\nDirectories:\n\t{}'.format('\n\t'.join(dirs)))
    else:
        click.echo('\nNo Directories in {}'.format(path or '/'))


@click.command(help='Output info about a dataset')
@click.argument('path', type=click.Path())
@click.option('--json/--no-json', 'output_json', default=False,
              help='Output as JSON.')
@click.option('--limit', type=int, default=10,
              help='Limit number of entities displayed')
@click.option('--relative/--no-relative', default=True)
@click.option('--path-is-sub', default=False, is_flag=True)
def describe(path, output_json, limit, relative, path_is_sub):
    pc = commands.get_pilot_client()
    entry = pc.get_search_entry(path, relative=relative,
                                path_is_sub=path_is_sub)
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
            get_formatted_fields(entry, cols, limit=limit) +
            [''] +
            get_single_file_info(entry, single_file_entry) +
            ['', ''] +
            get_location_info(entry)
        )
    else:
        cols = ['title', 'authors', 'publisher', 'subjects', 'dates',
                'formats', 'version', 'combined_size', 'description',
                'files']
        output = '\n'.join(
            get_formatted_fields(entry, cols, limit=limit) +
            [''] +
            get_location_info(entry)
        )

    click.echo(output)

import os
import urllib
import logging
import datetime

log = logging.getLogger(__name__)

FIELD_METADATA_TITLES = [
    ('name', 'Column Name'),
    ('type', 'Type'), ('count', 'Count'),
    ('frequency', 'Freq'), ('top', 'Top'),
    ('unique', 'Unique'),
    ('min', 'Min'),
    ('max', 'Max'),
    ('mean', 'Mean'),
    ('std', 'Std'),
    ('25', '25-PCTL'),
    ('50', '50-PCTL'),
    ('75', '75-PCTL')
 ]


def get_formatted_fields(entry, columns, formatting='{:21.20}{}', limit=10):
    output = []
    raw_data = dict(parse_result(entry, columns))
    tdata = zip(get_titles(columns),
                [raw_data[name] for name in columns])
    for title, data in tdata:
        if isinstance(data, list):
            if len(data) > limit:
                data.insert(0, 'List truncated due to number of items. '
                               'Showing 10/{}.'.format(len(data)))
                data = data[:limit]
            output += [formatting.format(title, line) for line in data[:1]]
            output += [formatting.format('', line) for line in data[1:]]
        else:
            output.append(formatting.format(title, data))
    return output


def get_formatted_field_metadata(field_metadata):
    fmt = ('{:21.20}'
           '{:8.7}{:7.6}{:5.4}{:12.11}{:7.6}'
           '{:7.6}{:8.7}{:8.7}{:8.7}')
    _, titles = zip(*FIELD_METADATA_TITLES)
    formatted_titles = [fmt.format(*titles)]

    data = []
    for row in get_field_metadata(field_metadata):
        _, fm_data = zip(*row)
        data.append(fmt.format(*[str(i) for i in fm_data]))
    if data:
        return formatted_titles + data
    return []


def get_titles(list_of_names):
    title_map = dict([(name, title) for name, title, _ in GENERAL_PARSE_FUNCS])
    return [title_map.get(name) for name in list_of_names]


def parse_result(result, fields=None):
    processed_results = []
    fields = fields or GENERAL_PARSE_FUNCS
    funcs_subset = [func for func in GENERAL_PARSE_FUNCS if func[0] in fields]
    for name, _, processor in funcs_subset:
        try:
            data = processor(result)
        except Exception:
            # log.exception(e)
            data = ''
        processed_results.append((name, data))
    return processed_results


def get_field_metadata(field_metadata):
    ret = []
    metadata_names = [n for n, _ in FIELD_METADATA_TITLES]
    for field_metadata_item in field_metadata.get('field_definitions', []):
        ret.append([(name, field_metadata_item.get(name, ''))
                    for name in metadata_names])
    return ret


def get_size(result):
    size = sum([f.get('length', 0) for f in result.get('files')])
    # 2**10 = 1024
    power = 2**10
    n = 0
    Dic_powerN = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1

    return '{} {}'.format(int(size), Dic_powerN[n])


def get_dates(result):
    dates = result['dc']['dates']
    fdates = []
    for date in dates:
        dt = datetime.datetime.strptime(date['date'], '%Y-%m-%dT%H:%M:%S.%fZ')
        fdates.append('{}: {: %A, %b %d, %Y}'.format(date['dateType'], dt))
    return fdates


def get_paths(result):
    return [urllib.parse.urlparse(f.get('url')).path
            for f in result.get('files')]


def get_common_path(result):
    paths = get_paths(result)
    common_path = paths[0]
    while common_path and not all([common_path in p for p in paths]):
        common_path = os.path.dirname(common_path)
    return common_path


def get_relative_paths(result):
    return [path.replace(get_common_path(result), '').lstrip('/')
            for path in get_paths(result)]


def get_formats(result):
    formats = [f['mime_type'] for f in result.get('files', {})
               if f.get('mime_type')]
    return ['{} ({})'.format(f, formats.count(f)) for f in set(formats)]


def get_files(result):
    listings = []
    common_path = get_common_path(result)
    for f in result.get('files', []):
        path = urllib.parse.urlparse(f.get('url')).path
        path = path.replace(common_path, '').lstrip('/')
        listings.append('{} ({})'.format(path, f.get('mime_type')))
    return sorted(listings)


GENERAL_PARSE_FUNCS = [
    ('title', 'Title', lambda r: r['dc']['titles'][0]['title']),
    ('authors', 'Authors',
     lambda r: [c['creatorName'] for c in r['dc']['creators']]),
    ('publisher', 'Publisher', lambda r: r['dc']['publisher']),
    ('subjects', 'Subjects',
     lambda r: [s['subject'] for s in r['dc']['subjects']]),
    ('dates', 'Dates', get_dates),
    ('data', 'Data',
     lambda r: r['project_metadata']['data_type']),
    ('dataframe', 'Dataframe',
     lambda r: r['project_metadata']['dataframe_type']),
    ('rows', 'Rows',
     lambda r: r['files'][0]['field_metadata']['numrows']),
    ('columns', 'Columns',
     lambda r: r['files'][0]['field_metadata']['numcols']),
    ('formats', 'Formats', get_formats),
    ('version', 'Version', lambda r: r['dc']['version']),
    ('size', 'Size', get_size),
    ('combined_size', 'Combined Size', get_size),
    ('files', 'Files', get_files),
    ('description', 'Description',
     lambda r: r['dc']['descriptions'][0]['description']),
]

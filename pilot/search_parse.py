
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


def get_field_metadata_titles():
    return [t for _, t in FIELD_METADATA_TITLES]


def get_titles(list_of_names):
    title_map = dict([(name, title) for name, title, _ in PARSE_FUNCS])
    return [title_map.get(name) for name in list_of_names]


def parse_result(result):
    processed_results = []
    for name, _, processor in PARSE_FUNCS:
        try:
            data = processor(result)
        except Exception as e:
            data = ''
            log.exception(e)
        processed_results.append((name, data))
    return processed_results


def get_field_metadata(result):
    field_metadata = get_single_file_rfm(result).get('field_metadata', {})
    ret = []
    metadata_names = [n for n, _ in FIELD_METADATA_TITLES]
    for field_metadata_item in field_metadata.get('field_definitions', []):
        ret.append([(name, field_metadata_item.get(name, ''))
                    for name in metadata_names])
    return ret


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


def get_dates(result):
    dates = result['dc']['dates']
    fdates = []
    for date in dates:
        dt = datetime.datetime.strptime(date['date'], '%Y-%m-%dT%H:%M:%S.%fZ')
        fdates.append('{}: {: %A, %b %d, %Y}'.format(date['dateType'], dt))
    return fdates


PARSE_FUNCS = [
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
     lambda r: get_single_file_rfm(r)['field_metadata']['numrows']),
    ('columns', 'Columns',
     lambda r: get_single_file_rfm(r)['field_metadata']['numcols']),
    ('formats', 'Formats', lambda r: r['dc']['formats']),
    ('version', 'Version', lambda r: r['dc']['version']),
    ('size', 'Size', get_size),
    ('description', 'Description',
     lambda r: r['dc']['descriptions'][0]['description']),
]

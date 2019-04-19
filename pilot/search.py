import os
import copy
import hashlib
import pytz
import datetime
import mimetypes
import jsonschema

from pilot.config import config
from pilot.validation import validate_dataset, validate_user_provided_metadata
from pilot.analysis import analyze_dataframe
from pilot.exc import RequiredUploadFields

DEFAULT_HASH_ALGORITHMS = ['sha256', 'md5']
DEFAULT_PUBLISHER = 'Argonne National Laboratory'
MINIMUM_USER_REQUIRED_FIELDS = [
    'dataframe_type',
    'data_type'
]

GMETA_LIST = {
    "@version": "2016-11-09",
    "ingest_type": "GMetaList",
    "ingest_data": {
        "@version": "2016-11-09",
        "gmeta": []
    }
}

GMETA_ENTRY = {
    "@version": "2016-11-09",
    "visible_to": [],
    "content": '',
    "subject": ''
}

GROUP_URN_PREFIX = 'urn:globus:groups:id:{}'

# Used for user provided metadata. These fields will be stripped out and used
# in the datacite fields.
DATACITE_FIELDS = ['title', 'description', 'formats']


def get_formatted_date():
    return datetime.datetime.now(pytz.utc).isoformat().replace('+00:00', 'Z')


def scrape_metadata(dataframe, url, dataframe_type, analyze_file=False):
    mimetype = mimetypes.guess_type(dataframe)[0]
    if mimetype is None:
        raise ValueError('Unable to determine Mimetype for "{}" (try adding '
                         'an extension)'.format(os.path.basename(dataframe)))

    user_info = config.get_user_info()
    name = user_info['name'].split(' ')
    if len(name) > 1 and ',' not in user_info['name']:
        # If the persons name is ['Samuel', 'L.', 'Jackson'], produces:
        # "Jackson, Samuel L."
        formal_name = '{}, {}'.format(name[-1:][0], ' '.join(name[:-1]))
    else:
        formal_name = user_info['name']
    metadata = analyze_dataframe(dataframe) if analyze_file else {}
    return {
        'dc': {
            'titles': [
                {
                    'title': os.path.basename(dataframe)
                }
            ],
            'creators': [
                {
                    'creatorName': formal_name
                }
            ],
            'publicationYear': str(datetime.datetime.now().year),
            'publisher': DEFAULT_PUBLISHER,
            'resourceType': {
                'resourceTypeGeneral': 'Dataset'
            },
            'dates': [
                {
                    'dateType': 'Created',
                    'date': get_formatted_date()
                }
            ],
            'formats': [
                mimetypes.guess_type(dataframe)[0]
            ],
            'version': '1'
        },
        'files': gen_remote_file_manifest(dataframe, url, dataframe_type),
        'field_metadata': metadata,
        'ncipilot': {},
    }


def update_metadata(new_metadata, prev_metadata, user_metadata, files_updated):
    metadata = copy.deepcopy(new_metadata)
    if prev_metadata:
        metadata.update(prev_metadata)
        if files_updated:
            version = int(metadata['dc']['version'])
            metadata['dc']['version'] = str(version + 1)
            metadata['dc']['dates'].append({
                'dateType': 'Updated',
                'date': get_formatted_date()
            })
            metadata['files'] = new_metadata['files']
    if user_metadata:
        validate_user_provided_metadata(user_metadata)
        for field_name, value in user_metadata.items():
            if field_name in DATACITE_FIELDS:
                set_dc_field(metadata, field_name, value)
            else:
                if not metadata.get('ncipilot'):
                    metadata['ncipilot'] = {}
                metadata['ncipilot'][field_name] = value
    return metadata


def gen_gmeta(subject, visible_to, content):
    try:
        validate_dataset(content)
    except jsonschema.exceptions.ValidationError as ve:
        if any([m in ve.message for m in MINIMUM_USER_REQUIRED_FIELDS]):
            raise RequiredUploadFields(MINIMUM_USER_REQUIRED_FIELDS) from None
    entry = GMETA_ENTRY.copy()
    entry['visible_to'] = [GROUP_URN_PREFIX.format(visible_to)]
    entry['subject'] = subject
    entry['content'] = content
    gmeta = GMETA_LIST.copy()
    gmeta['ingest_data']['gmeta'].append(entry)
    return gmeta


def set_dc_field(metadata, field_name, value):
    dc_fields = {
        'title': gen_dc_title,
        'description': gen_dc_description,
        'formats': gen_dc_formats,
    }
    if field_name not in dc_fields.keys():
        raise NotImplementedError('Cannot resolve field {}'.format(field_name))
    return dc_fields[field_name](metadata, value)


def gen_dc_title(metadata, title):
    metadata['dc']['titles'] = [{'title': title}]


def gen_dc_description(metadata, description):
    metadata['dc']['descriptions'] = [{'description': description,
                                       'descriptionType': 'Other'}]


def gen_dc_formats(metadata, formats):
    metadata['dc']['formats'] = formats


def gen_remote_file_manifest(filepath, url, data_type, metadata={},
                             algorithms=DEFAULT_HASH_ALGORITHMS):
    rfm = metadata.copy()
    rfm.update({alg: compute_checksum(filepath, getattr(hashlib, alg)())
                for alg in algorithms})
    rfm.update({
        'filename': os.path.basename(filepath),
        'data_type': data_type,
        'url': url,
        'length': os.stat(filepath).st_size
    })
    return [rfm]


def compute_checksum(file_path, algorithm, block_size=65536):
    if not algorithm:
        algorithm = hashlib.sha256()
    with open(os.path.abspath(file_path), 'rb') as open_file:
        buf = open_file.read(block_size)
        while len(buf) > 0:
            algorithm.update(buf)
            buf = open_file.read(block_size)
    open_file.close()
    return algorithm.hexdigest()

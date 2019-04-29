import os
import copy
import hashlib
import pytz
import datetime
import mimetypes
import json
import jsonschema
import logging

from pilot.validation import validate_dataset, validate_user_provided_metadata
from pilot.analysis import analyze_dataframe
from pilot.exc import RequiredUploadFields
import pilot

DEFAULT_HASH_ALGORITHMS = ['sha256', 'md5']
FOREIGN_KEYS_FILE = os.path.join(os.path.dirname(__file__),
                                 'foreign_keys.json')
DEFAULT_PUBLISHER = 'Argonne National Laboratory'
MINIMUM_USER_REQUIRED_FIELDS = [
    'dataframe_type',
    'data_type',
    'mime_type',
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
DATACITE_FIELDS = ['title', 'description', 'creators', 'mime_type']
# Used for user provided metadata. Fields here will be copied into the rfm,
# even if also provided in other areas.
REMOTE_FILE_MANIFEST_FIELDS = ['mime_type', 'data_type']

log = logging.getLogger(__name__)


def get_formatted_date():
    return datetime.datetime.now(pytz.utc).isoformat().replace('+00:00', 'Z')


def get_foreign_keys(filename=FOREIGN_KEYS_FILE, test=False):
    with open(filename) as fh:
        fkeys = json.load(fh)
    pc = pilot.client.PilotClient()
    for fkey_data in fkeys.values():
        path = fkey_data['reference']['resource']
        dirname, fname, = os.path.dirname(path), os.path.basename(path)
        sub = pc.get_subject_url(fname, dirname, test)
        fkey_data['reference']['resource'] = sub
    return fkeys


def scrape_metadata(dataframe, url, skip_analysis=True, test=False):
    mimetype = mimetypes.guess_type(dataframe)[0]
    dc_formats = []
    rfm_metadata = {}
    if mimetype:
        dc_formats.append(mimetype)
        rfm_metadata['mime_type'] = mimetype

    user_info = pilot.config.config.get_user_info()
    name = user_info['name'].split(' ')
    if len(name) > 1 and ',' not in user_info['name']:
        # If the persons name is ['Samuel', 'L.', 'Jackson'], produces:
        # "Jackson, Samuel L."
        formal_name = '{}, {}'.format(name[-1:][0], ' '.join(name[:-1]))
    else:
        formal_name = user_info['name']
    fkeys = get_foreign_keys(test=test)
    metadata = analyze_dataframe(dataframe, fkeys) if not skip_analysis else {}
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
            'subjects': [
                {
                    "subject": "machine learning"
                },
                {
                    "subject": "genomics"
                }
            ],
            'publicationYear': str(datetime.datetime.now().year),
            'publisher': DEFAULT_PUBLISHER,
            'resourceType': {
                'resourceType': 'Dataset',
                'resourceTypeGeneral': 'Dataset'
            },
            'dates': [
                {
                    'dateType': 'Created',
                    'date': get_formatted_date()
                }
            ],
            'formats': dc_formats,
            'version': '1'
        },
        'files': gen_remote_file_manifest(dataframe, url,
                                          metadata=rfm_metadata),
        'field_metadata': metadata,
        'ncipilot': {},
    }


def carryover_old_file_metadata(new_scrape_rfm, old_rfm):
    """Carries over old metadata into the new file manifest. This is
    desired if the files haven't changed and the metadata wasn't explicitly
    added to the new metadata, in which case we don't want to loose the old
    descriptive metadata. If the Remote File Manifests have different files,
    this should not be used."""
    if not old_rfm or not new_scrape_rfm:
        return new_scrape_rfm

    new = {f['url']: f for f in new_scrape_rfm}
    old = {f['url']: f for f in old_rfm}

    if new.keys() != old.keys():
        log.debug('Files Updated! Old: {}, New: {}'
                  ''.format(list(old_rfm), list(new_scrape_rfm)))
        return new_scrape_rfm

    for k, v in old.items():
        for field in ['data_type', 'mime_type']:  # 'dataframe_type'
            if old[k].get(field):
                if new.get(k):
                    new[k][field] = old[k][field]
    return list(new.values())


def files_modified(manifest1, manifest2):
    """Compare two remote file manifests for equality, and return true if
    the files are different. ONLY file specific properties are checked,
    such as url, filename, length, and hash.
    if one contains more metadata than another but everything else matches,
    this will return False.
    FIXME: This can only check two manifests that have the same kinds of hashes
    If one has md5, and the other doesn't, this will fail."""
    if manifest1 is None and manifest2 is None:
        return False

    if manifest1 is None or manifest2 is None:
        return True

    man1 = {f['url']: f for f in manifest1}
    man2 = {f['url']: f for f in manifest2}

    if man1.keys() != man2.keys():
        return True

    fields = ['url', 'filename', 'length'] + list(hashlib.algorithms_available)

    for url_key in man1.keys():
        man1dict, man2dict = man1.get(url_key), man2.get(url_key)
        if any([man1dict.get(f) != man2dict.get(f) for f in fields]):
            return True


def update_dc_version(metadata):
    version = int(metadata['dc']['version'])
    metadata['dc']['version'] = str(version + 1)
    metadata['dc']['dates'].append({
        'dateType': 'Updated',
        'date': get_formatted_date()
    })


def update_metadata(scraped_metadata, prev_metadata, user_metadata):
    if prev_metadata:
        metadata = copy.deepcopy(scraped_metadata or {})

        files_updated = files_modified(scraped_metadata.get('files'),
                                       metadata.get('files'))
        if files_updated:
            # If files have been modified, don't carryover metadata fields
            update_dc_version(metadata)
        metadata['files'] = carryover_old_file_metadata(
            scraped_metadata.get('files'),
            prev_metadata.get('files')
        )
    else:
        metadata = scraped_metadata
    if user_metadata:
        validate_user_provided_metadata(user_metadata)
        for field_name, value in user_metadata.items():
            if field_name in DATACITE_FIELDS:
                set_dc_field(metadata, field_name, value)
            if field_name in REMOTE_FILE_MANIFEST_FIELDS:
                for manifest in metadata['files']:
                    manifest[field_name] = value
            if field_name not in DATACITE_FIELDS + REMOTE_FILE_MANIFEST_FIELDS:
                if not metadata.get('ncipilot'):
                    metadata['ncipilot'] = {}
                metadata['ncipilot'][field_name] = value
            # TODO Remove this once we swith to having these fields in rfms
            if field_name in ['data_type']:
                if not metadata.get('ncipilot'):
                    metadata['ncipilot'] = {}
                metadata['ncipilot'][field_name] = value
    metadata['ncipilot'] = metadata.get('ncipilot', {})
    return metadata


def gen_gmeta(subject, visible_to, content):
    try:
        validate_dataset(content)
    except jsonschema.exceptions.ValidationError as ve:
        if any([m in ve.message for m in MINIMUM_USER_REQUIRED_FIELDS]):
            raise RequiredUploadFields(ve.message,
                                       MINIMUM_USER_REQUIRED_FIELDS) from None
    entry = GMETA_ENTRY.copy()
    entry['visible_to'] = [GROUP_URN_PREFIX.format(visible_to)]
    entry['subject'] = subject
    entry['content'] = content
    entry['id'] = 'metadata'
    gmeta = GMETA_LIST.copy()
    gmeta['ingest_data']['gmeta'].append(entry)
    return gmeta


def set_dc_field(metadata, field_name, value):
    dc_fields = {
        'title': gen_dc_title,
        'description': gen_dc_description,
        'creators': gen_dc_creators,
        'mime_type': gen_dc_formats,
    }
    if field_name not in dc_fields.keys():
        raise NotImplementedError('Cannot resolve field {}'.format(field_name))
    return dc_fields[field_name](metadata, value)


def gen_dc_title(metadata, title):
    metadata['dc']['titles'] = [{'title': title}]


def gen_dc_description(metadata, description):
    metadata['dc']['descriptions'] = [{'description': description,
                                       'descriptionType': 'Other'}]


def gen_dc_creators(metadata, creators):
    metadata['dc']['creators'] = creators


def gen_dc_formats(metadata, formats):
    if isinstance(formats, str):
        formats = [formats]
    metadata['dc']['formats'] = formats


def gen_remote_file_manifest(filepath, url, metadata={},
                             algorithms=DEFAULT_HASH_ALGORITHMS):
    rfm = metadata.copy()
    rfm.update({alg: compute_checksum(filepath, getattr(hashlib, alg)())
                for alg in algorithms})
    rfm.update({
        'filename': os.path.basename(filepath),
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

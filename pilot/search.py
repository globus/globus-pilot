"""
search.py is primarily concerned with analyzing local files, generating
metadata, combining metadata, and preparing gmeta entries for ingest into
Globus Search.
"""

import os
import copy
import hashlib
import urllib
import difflib
import pytz
import datetime
import jsonschema
import logging

from pilot.validation import validate_dataset, validate_user_provided_metadata
from pilot import analysis
from pilot.exc import InvalidField, PilotClientException

DEFAULT_HASH_ALGORITHMS = ['sha256', 'md5']
DEFAULT_PUBLISHER = 'Argonne National Laboratory'
# Previously users were required to add certain fields. If we want to add those
# back, add them here.
MINIMUM_USER_REQUIRED_FIELDS = []

GMETA_LIST = {
    # "@version": "2016-11-09",
    "ingest_type": "GMetaList",
    "ingest_data": {
        # "@version": "2016-11-09",
        "gmeta": []
    }
}

GMETA_ENTRY = {
    # "@version": "2016-11-09",
    "visible_to": [],
    "content": '',
    "subject": ''
}

GROUP_URN_PREFIX = 'urn:globus:groups:id:{}'

CORE_PILOT_FIELDS = ['dc', 'project_metadata', 'files']
# Used for user provided metadata. These fields will be stripped out and used
# in the datacite fields.
DATACITE_FIELDS = ['title', 'description', 'creators', 'mime_type',
                   'publisher', 'subjects', 'publicationYear', 'resourceType',
                   'dates', 'version', 'descriptions']
# Used for user provided metadata. Fields here will be copied into the rfm,
# even if also provided in other areas.
REMOTE_FILE_MANIFEST_FIELDS = ['mime_type']

log = logging.getLogger(__name__)


def get_formatted_date():
    return datetime.datetime.now(pytz.utc).isoformat().replace('+00:00', 'Z')


def suggest_shortname(existing_shortnames, non_existent_shortname):

    matches = {
        difflib.SequenceMatcher(None, es, non_existent_shortname).ratio(): es
        for es in existing_shortnames
    }
    suggestion = ''
    if matches:
        suggestion = 'Did you mean {}?'.format(
            matches.get(max(matches.keys()))
        )
    return suggestion


def get_foreign_keys(entry_files, foreign_keys, existing_paths):
    files = copy.deepcopy(entry_files)
    for filem in files:
        defs = filem.get('field_metadata', {}).get('field_definitions')
        if not defs:
            continue
        for field_def in defs:
            foreign_f = field_def.get('name')
            if not foreign_keys.get(foreign_f):
                continue
            ref = copy.deepcopy(foreign_keys[foreign_f]['reference'])
            if ref['resource'] in existing_paths:
                field_def['reference'] = ref
            else:
                sug = suggest_shortname(existing_paths,
                                        os.path.basename(ref['resource']))
                raise Exception('Reference {} did not resolve. {}'
                                .format(ref['resource'], sug))
    return files


def scrape_metadata(dataframe, url, profile, project, skip_analysis=True):
    """
    Gather metadata on 'dataframe', including generati
    :param dataframe:
    :param url:
    :param profile:
    :param project:
    :param foreign_keys:
    :param skip_analysis:
    :return:
    """
    name = profile.name.split(' ')
    if len(name) > 1 and ',' not in profile.name:
        # If the persons name is ['Samuel', 'L.', 'Jackson'], produces:
        # "Jackson, Samuel L."
        formal_name = '{}, {}'.format(name[-1:][0], ' '.join(name[:-1]))
    else:
        formal_name = profile.name
    remote_file_manifest = gen_remote_file_manifest(
        dataframe, url, skip_analysis=skip_analysis
    )
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
            'publisher': (profile.organization or DEFAULT_PUBLISHER),
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
            'formats': sorted(list({f['mime_type']
                                    for f in remote_file_manifest
                                    if f.get('mime_type')})),
            'version': '1'
        },
        'files': remote_file_manifest,
        'project_metadata': {
            'project-slug': project
        },
    }


def prune_files(entry, path):
    path = path.lstrip('/').rstrip('/')
    remaining = []
    for f in entry.get('files'):
        url_path = urllib.parse.urlparse(f.get('url')).path.lstrip('/')
        if not url_path.startswith(path):
            log.debug('{} not in {}, keeping file...'.format(f['url'], path))
            remaining.append(f)
    return remaining


def carryover_old_file_metadata(new_scrape_rfm, old_rfm):
    """Carries over old metadata into the new file manifest. This is
    desired if the files haven't changed and the metadata wasn't explicitly
    added to the new metadata, in which case we don't want to loose the old
    descriptive metadata. If the Remote File Manifests have different files,
    this should not be used."""
    if not old_rfm or not new_scrape_rfm:
        return new_scrape_rfm or old_rfm

    new = {f['url']: f for f in new_scrape_rfm}
    old = {f['url']: f for f in old_rfm}

    similar_files = set(old.keys()).intersection(set(new.keys()))
    DO_NOT_CARRYOVER = DEFAULT_HASH_ALGORITHMS + ['filename', 'length']
    for url in similar_files:
        for field in old[url].keys():
            if field in DO_NOT_CARRYOVER:
                continue
            if old[url].get(field):
                if new.get(url):
                    new[url][field] = old[url][field]

    # Carry over old files
    for url in old.keys():
        if url not in new.keys():
            new[url] = old[url]
    return list(new.values())


def overwrite_core_fields(new_metadata, old_metadata):
    """For fields like dc and project_metadata, if overwrite the items in
    old_metadata with the fields in new_metadata"""
    old_metadata = copy.deepcopy(old_metadata)
    for cat in ['dc', 'project_metadata']:
        if cat not in new_metadata:
            continue
        for newk, newv in new_metadata[cat].items():
            log.debug('Replacing old field [{}][{}] with {}'.format(cat, newk,
                                                                    newv))
            old_metadata[cat][newk] = newv
    return old_metadata


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
    return False


def metadata_modified(new_metadata, old_metadata):
    """Check if the new metadata passed in matches the old metadata. Returns
    true if all fields match except for timestamps on dates, which are allowed
    to differ between one another.
    Both new_metadata and old_metadata should be dicts that match the output
    from `scrape_metadata` and can pass validation
    """
    if not new_metadata:
        log.debug('No new metadata, aborting...')
        return bool(old_metadata)
    old_metadata = old_metadata or {}
    general_fields_match = [new_metadata.get(field) == old_metadata.get(field)
                            for field in ['files', 'project_metadata']]
    dc_fields_match = [
        new_metadata['dc'][key] == old_metadata.get('dc', {}).get(key)
        for key in new_metadata['dc'].keys() if key != 'dates'
    ]
    old_dates = old_metadata.get('dc', {}).get('dates', [])
    date_entry_lengths_eq = len(new_metadata['dc']['dates']) == len(old_dates)
    zipped_dates = zip(new_metadata['dc']['dates'], old_dates)
    date_types_match = [nm['dateType'] == om['dateType']
                        for nm, om in zipped_dates]
    matches = [
        all(general_fields_match),
        all(dc_fields_match),
        date_entry_lengths_eq,
        all(date_types_match)
    ]
    log.debug('Metadata comparison: files/metadata: {}, dc: {}, '
              'date entries: {}, date types: {}'.format(*matches))
    return not all(matches)


def update_dc_version(new_metadata, old_metadata):
    """
    Compare new metadata with old metadata, and derive a new version number.
    If files have changed in the old metadata, returns new metadata with
    bumped version. Otherwise, simply carries over the old metadata version
    number.
    """
    files_updated = files_modified(new_metadata.get('files'),
                                   old_metadata.get('files'))
    version = int(old_metadata['dc']['version'])
    if files_updated:
        new_metadata['dc']['version'] = str(version + 1)
        new_metadata['dc']['dates'].append({
            'dateType': 'Updated',
            'date': get_formatted_date()
        })
    else:
        new_metadata['dc']['version'] = old_metadata['dc']['version']
    return new_metadata


def update_metadata(scraped_metadata, prev_metadata, user_metadata):
    if not scraped_metadata and not prev_metadata:
        raise PilotClientException('No scraped or previous metadata!')
    elif not scraped_metadata:
        metadata = prev_metadata
    elif not prev_metadata:
        metadata = scraped_metadata
    else:
        log.debug('Previous metadata detected!')
        metadata = copy.deepcopy(scraped_metadata or {})
        if scraped_metadata:
            metadata = update_dc_version(metadata, prev_metadata)
        metadata['files'] = carryover_old_file_metadata(
            scraped_metadata.get('files'),
            prev_metadata.get('files')
        )
    if user_metadata:
        metadata = overwrite_core_fields(user_metadata, metadata)
        user_metadata = copy.deepcopy(user_metadata)
        for coref in CORE_PILOT_FIELDS:
            if coref in user_metadata:
                user_metadata.pop(coref)
        validate_user_provided_metadata(user_metadata)
        for field_name, value in user_metadata.items():
            if field_name in DATACITE_FIELDS:
                set_dc_field(metadata, field_name, value)
            if field_name in REMOTE_FILE_MANIFEST_FIELDS:
                for manifest in metadata['files']:
                    manifest[field_name] = value
            if field_name not in DATACITE_FIELDS + REMOTE_FILE_MANIFEST_FIELDS:
                if not metadata.get('project_metadata'):
                    metadata['project_metadata'] = {}
                metadata['project_metadata'][field_name] = value
            # TODO Remove this once we swith to having these fields in rfms
            if field_name in ['data_type']:
                if not metadata.get('project_metadata'):
                    metadata['project_metadata'] = {}
                metadata['project_metadata'][field_name] = value
    metadata['project_metadata'] = metadata.get('project_metadata', {})
    return metadata


def gather_metadata_stats(new_metadata, previous_metadata):
    """
    Gather general differences between new_metadata and previous metadata.
    Both arguments must be valid search data, either returned from
    PilotClient.get_search_entry() or search.scrape_metadata().
    Returns the following info:
    * record_exists: True if previous metadata is not empty
    * previous_metadata: The previous metadata
    * new_metadata: The new metadata
    * metadata_modified: True if metadata was modified, false otherwise
    * files_modified: True if file content has changed, false otherwise.
    * version: The version listed on the previous metadata, if it exists
    * new_version: The version listed on the new metadata
    """
    return {
        'record_exists': True if previous_metadata else False,
        'previous_metadata': previous_metadata,
        'new_metadata': new_metadata,
        'metadata_modified': metadata_modified(new_metadata,
                                               previous_metadata),
        'files_modified': files_modified(
            new_metadata.get('files'), previous_metadata.get('files')),
        'version': (previous_metadata.get('dc', {}).get('version')
                    if previous_metadata else None),
        'new_version': new_metadata.get('dc', {}).get('version'),
    }


def gen_gmeta(subject, visible_to, content, validate=True):
    log.warning('Deprecated. Please use pilot.search.get_gmeta_list instead.')
    return get_gmeta_list([{
        'subject': subject,
        'visible_to': visible_to,
        'content': content
    }], validate=validate)


def get_gmeta_list(content_list, default_visible_to=None, validate=True):
    default_visible_to = default_visible_to or 'public'
    gmeta_entries = []
    for ent in content_list:
        try:
            validate_dataset(ent['content'])
        except jsonschema.exceptions.ValidationError as ve:
            log.error('Error processing subject {}'.format(ent['subject']))
            if not validate:
                log.exception(ve)
                log.warning('Validation FAILED, but validation is disabled! '
                            'Make sure you really want to ingest {}'
                            ''.format(ent['subject']))
            else:
                raise
        visible_to = ent.get('visible_to', default_visible_to)
        if isinstance(visible_to, str):
            visible_to = [visible_to]
        vt_list = []
        for vt in visible_to:
            if vt == 'public' or vt.startswith('urn:globus:'):
                vt_list.append(vt)
            else:
                vt_list.append(GROUP_URN_PREFIX.format(vt))
        entry = copy.deepcopy(GMETA_ENTRY)
        entry['visible_to'] = vt_list
        entry['subject'] = ent['subject']
        entry['content'] = ent['content']
        entry['id'] = ent.get('id', 'metadata')
        gmeta_entries.append(entry)
    gmeta_list_doc = copy.deepcopy(GMETA_LIST)
    gmeta_list_doc['ingest_data']['gmeta'] = gmeta_entries
    return gmeta_list_doc


def set_dc_field(metadata, field_name, value):
    """In an effort to make things more user friendly, the user is allowed to
    set some dc fields incorrectly. For example in "formats", even though dc
    specifies a list, the user can use a string instead and it will be
    automatically corrected."""
    dc_fields = {
        'title': gen_dc_title,
        'description': gen_dc_description,
        'descriptions': gen_dc_description,
        'creators': gen_dc_creators,
        'mime_type': gen_dc_formats,
        'publisher': gen_dc_publisher,
        'subjects': gen_dc_subjects,
        'publicationYear': gen_dc_publication_year,
        'resourceType': gen_dc_resource_type,
        'dates': gen_dc_dates,
        'version': gen_dc_version,
    }
    if field_name not in dc_fields.keys():
        raise NotImplementedError('Cannot resolve field {}'.format(field_name))
    return dc_fields[field_name](metadata, value)


def gen_dc_title(metadata, title):
    metadata['dc']['titles'] = [{'title': title}]


def gen_dc_description(metadata, description):
    if isinstance(description, str):
        metadata['dc']['descriptions'] = [{'description': description,
                                           'descriptionType': 'Other'}]
    else:
        metadata['dc']['descriptions'] = description


def gen_dc_creators(metadata, creators):
    metadata['dc']['creators'] = creators


def gen_dc_publisher(metadata, publisher):
    metadata['dc']['publisher'] = publisher


def gen_dc_subjects(metadata, subjects):
    metadata['dc']['subjects'] = subjects


def gen_dc_publication_year(metadata, pub_year):
    metadata['dc']['publicationYear'] = pub_year


def gen_dc_resource_type(metadata, resource_type):
    metadata['dc']['resourceType'] = resource_type


def gen_dc_dates(metadata, dates):
    metadata['dc']['dates'] = dates


def gen_dc_version(metadata, version):
    try:
        int(version)
    except ValueError:
        raise InvalidField('"version" must be a number') from None
    metadata['dc']['version'] = str(version)


def gen_dc_formats(metadata, formats):
    if isinstance(formats, str):
        formats = [formats]
    metadata['dc']['formats'] = formats


def gen_remote_file_manifest(filepath, url, algorithms=DEFAULT_HASH_ALGORITHMS,
                             skip_analysis=True):
    manifest_entries = []
    for subfile, remote_short_path in get_subdir_paths(filepath):
        rfm = {alg: compute_checksum(subfile, getattr(hashlib, alg)())
               for alg in algorithms}
        mimetype = analysis.mimetypes.detect_type(subfile)
        metadata = (analysis.analyze_dataframe(subfile, mimetype)
                    if not skip_analysis else {})
        rfm.update({
            'filename': os.path.basename(subfile),
            'url': os.path.join(os.path.dirname(url), remote_short_path),
            'field_metadata': metadata,
            'mime_type': mimetype
        })
        if os.path.exists(subfile):
            rfm['length'] = os.stat(subfile).st_size
        manifest_entries.append(rfm)
    return manifest_entries


def get_files(path):
    """Walk a directory to get all files in a directory. """
    if os.path.isfile(path):
        return [path]
    else:
        file_lists = [[os.path.join(dirpath, f) for f in files]
                      for dirpath, _, files in os.walk(path)]
        # Flatten list of lists into a single list
        return [item for sublist in file_lists for item in sublist]


def get_subdir_paths(path):
    """Walk a directory to get all files, but return both the real path and
    the relative short_path. the short_path can be passed to the pilot client
    path methods to get the fully resolved remote path of the file."""
    local_path = os.path.dirname(path)
    return [(local_abspath, local_abspath.replace(local_path, '').lstrip('/'))
            for local_abspath in get_files(path)]


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

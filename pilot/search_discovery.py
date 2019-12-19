import os
import urllib
import logging

log = logging.getLogger(__name__)


def get_sub_in_collection(subject, entries, precise=True):
    """
    Look for a subject in a bunch of search entries.
    If 'subject' refers to a file, this looks for an exact subject match in
    entries and returns the content if it exists. If 'subject' is a multi-file
    collection subject must either match the top level folder or a file within
    the collection (or a non-existent file within the collection if
    precise=False).
    **Parameters**
    ``subject`` (*string*)
      A Globus Search URL
    ``entries`` (*string*)
      A list of Globus Search GMeta entries.
    ``precise`` (*bool*)
      If the path given points to a location inside a multi-file directory
      only return the record if the location matches a file.
      For example, given an entry containing the files:
        my_dir/foo1.txt, my_dir/foo2.txt, my_dir/foo3.txt
      If precise=True and the path is my_dir/foo4.txt, None will be
      returned. If precise=False and the path is my_dir/foo4.txt, the
      "my_dir" record will still be returned.
    """
    entry = get_entry_with_matching_subject(entries, subject)
    if entry is None or precise is False:
        return entry
    urls = [m.get('url') for m in entry['content'][0].get('files', [])]
    sub_path = urllib.parse.urlparse(subject).path
    for url in urls:
        log.debug('Checking {}'.format(url))
        if sub_path in url:
            log.debug('Found specific file in entry: {}'.format(url))
            return entry


def get_entry_with_matching_subject(entries, subject):
    """
    Get an entry with a matching subject. A matching subject is both an exact
    match and a path to a file within the subject. For example, given the
    subject:
      globus://foo-project-endpoint/foo_subject
    These would all be valid matches:
      globus://foo-project-endpoint/foo_subject
      globus://foo-project-endpoint/foo_subject/foo.txt
      globus://foo-project-endpoint/foo_subject/bar.txt
      globus://foo-project-endpoint/foo_subject/sub_folder/foo.txt
    NOTE! The actual file inside a subject does not need to exist for a match
    to happen. globus://foo-project-endpoint/foo_subject/bar.txt will return
    a match whether or not 'bar.txt' exists in the 'files' manifest.
    """
    sub_map, directory = {ent['subject']: ent for ent in entries}, subject
    # If the given subject is a path within a search entry, this will derive
    # which subject its part of.
    while directory and directory not in sub_map.keys():
        directory = os.path.dirname(directory)

    matches = list(filter(lambda sub: sub == directory, sub_map.keys()))
    if len(matches) == 1:
        return sub_map[matches[0]]
    log.debug('Match Fail: Sub {} matched {}/{} subs, not 1: {}'
              ''.format(subject, len(matches), len(entries), matches))


def get_matching_file(url, entry):
    files = get_matching_files(url, entry)
    if len(files) == 1:
        return files[0]


def get_matching_files(url, entry):
    """Given a search entry returned from PilotClient.get_search_entry, find
    all of the partial matches in the entry. Partial matches can happen if
    a base folder matches, but not the files below it. For example:
      * A url: http://example.com/files/foo
      * entry with files: http://example.com/files/foo/bar.txt
                          http://example.com/files/foo/moo.hdf5"""
    if entry and entry.get('files'):
        return [f for f in entry['files'] if url in f['url']]
    return []


def get_relative_filenames(url, entry):
    base_url = os.path.dirname(url)
    return [f['url'].replace(base_url, '').lstrip('/')
            for f in get_matching_files(url, entry)]


def get_paths(entry):
    return [urllib.parse.urlparse(f.get('url')).path
            for f in entry.get('files', [])]


def is_top_level(entry, subject):
    sub_path = urllib.parse.urlparse(subject).path
    return all([f_path.startswith(sub_path) for f_path in get_paths(entry)])

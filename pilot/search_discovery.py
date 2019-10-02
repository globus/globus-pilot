import os
import urllib
import logging

log = logging.getLogger(__name__)


def get_sub_in_collection(subject, entries):
    subs = [ent['subject'] for ent in entries]
    dir_sub = os.path.dirname(subject)
    while dir_sub and dir_sub not in subs:
        dir_sub = os.path.dirname(dir_sub)
    if subs.count(dir_sub) == 1:
        log.debug('Found subject (partial) {} in project.'.format(dir_sub))
        dir_ent = entries[subs.index(dir_sub)]['content'][0]
        urls = [m.get('url') for m in dir_ent.get('files', [])]
        sub_path = urllib.parse.urlparse(subject).path
        for url in urls:
            if sub_path in url:
                log.debug('Found specific file in subject: {}'.format(url))
                return dir_ent


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

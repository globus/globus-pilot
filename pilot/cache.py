import os
import time
import json
import logging

log = logging.getLogger(__name__)


class FileCache(object):
    def __init__(self, ttl=10, filename='cache.json'):
        self.ttl = ttl
        self.filename = filename

    def get(self, name, default=None):
        try:
            return self.__getitem__(name)
        except Exception:
            return default

    def __getitem__(self, name):
        if not os.path.exists(self.filename):
            raise KeyError('No Cache Exists!')
        with open(self.filename) as fh:
            cache = json.load(fh)
        now = time.time()
        if cache.get(name):
            log.debug('Cache item {} exists'.format(name))
            last_updated = cache[name].get('last_updated')
            if now - last_updated < self.ttl:
                return cache[name]['data']
            log.debug('Cache Expired')
        raise KeyError(name)

    def __setitem__(self, name, value):
        with open(self.filename, 'w+') as fh:
            try:
                cache = json.load(fh)
            except json.decoder.JSONDecodeError:
                cache = {}
            cache[name] = {'last_updated': time.time(),
                           'data': value}
            json.dump(cache, fh, indent=4)

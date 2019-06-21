import os
from configobj import ConfigObj
from fair_research_login import ConfigParserTokenStorage

from pilot.version import __version__


class Config():
    CFG_FILENAME = os.path.expanduser('~/.pilot1.cfg')

    def __init__(self, filename=None):
        self.filename = filename or self.CFG_FILENAME
        cfg = self.load()

        if not cfg:
            cfg['pilot'] = {'version': __version__}
            self.save(cfg)

    def migrate_to_configobj(self):
        cfg = self.load()
        old_cfg = ConfigParserTokenStorage(filename=self.CFG_FILENAME)
        cfg['tokens'] = old_cfg.read_tokens()
        cfg['pilot'] = {'version': __version__}
        cfg.write()

    def get_migrator(self):
        """Read the config and fetch the next migration based on the current
        config version."""
        cfg = self.load()
        if cfg and not cfg.get('pilot'):
            return self.migrate_to_configobj

    def migrate(self):
        """Migrate to the newest config version"""
        while not self.is_migrated():
            migrator = self.get_migrator()
            migrator()

    def is_migrated(self):
        return False if self.get_migrator() else True

    def save(self, cfg):
        cfg.write()

    def load(self):
        return ConfigObj(self.filename)

    def read_tokens(self):
        tokens = self.load().get('tokens', {})
        for tset in tokens:
            tokens[tset]['expires_at_seconds'] = \
                int(tokens[tset]['expires_at_seconds'])
        return tokens

    def write_tokens(self, tokens):
        cfg = self.load()
        cfg['tokens'] = tokens
        cfg.write()

    def clear_tokens(self):
        self.write_tokens({})

    def clear(self):
        cfg = self.load()
        cfg['tokens'] = {}
        cfg.write()


class ConfigSection:

    SECTION = None

    def __init__(self):
        self.config = Config()
        if not self.SECTION:
            raise NotImplementedError('SECTION must be set on Config Section '
                                      'obj')
        if self.SECTION not in self.config.load():
            cfg = self.config.load()
            cfg[self.SECTION] = {}
            self.config.save(cfg)

    def save_option(self, option, value, section=None):
        cfg = self.config.load()
        section = section or self.SECTION
        if cfg.get(section) is None:
            cfg[section] = {}
        cfg[section][option] = value
        self.config.save(cfg)

    def load_option(self, option, section=None):
        return self.config.load().get(section or self.SECTION, {}).get(option)

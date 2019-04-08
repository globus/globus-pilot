import os
from fair_research_login import ConfigParserTokenStorage


class Config(ConfigParserTokenStorage):
    CFG_FILENAME = os.path.expanduser('~/.pilot1.cfg')

    def get_user_info(self):
        cfg = self.load()
        if 'profile' in cfg:
            return dict(self.load()['profile'])
        return {}

    def save_user_info(self, user_info):
        cfg = self.load()
        cfg['profile'] = user_info
        self.save(cfg)

    def clear(self):
        cfg = self.load()
        cfg.clear()
        self.save(cfg)


config = Config(filename=Config.CFG_FILENAME, section='tokens')

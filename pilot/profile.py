from pilot.config import config


class Profile:

    def __init__(self):
        cfg = config.load()
        if 'profile' not in cfg.sections():
            cfg['profile'] = {}
            config.save(cfg)

    def load_user_info(self):
        return dict(config.load()['profile'])

    def save_user_info(self, user_info):
        old_info = self.load_user_info()
        if user_info['sub'] != old_info.get('sub'):
            cfg = config.load()
            cfg['profile'] = user_info
            # Also clear transfer logs
            cfg['transfer_log'] = {}
            config.save(cfg)

    def load_option(self, option):
        return self.load_user_info().get(option)

    def save_option(self, option, value):
        cfg = config.load()
        cfg['profile'][option] = value
        config.save(cfg)

    @property
    def name(self):
        return self.load_user_info()['name']

    @name.setter
    def name(self, value):
        self.save_option('name', value)

    @property
    def organization(self):
        return self.load_option('organization')

    @organization.setter
    def organization(self, value):
        self.save_option('organization', value)


profile = Profile()

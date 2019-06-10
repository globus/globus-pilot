import pilot


class Profile:

    def __init__(self):
        cfg = pilot.config.config.load()
        if 'profile' not in cfg.sections():
            cfg['profile'] = {}
            pilot.config.config.save(cfg)

    def load_user_info(self):
        return dict(pilot.config.config.load()['profile'])

    def save_user_info(self, user_info):
        old_info = self.load_user_info()
        if user_info['sub'] != old_info.get('sub'):
            cfg = pilot.config.config.load()
            cfg['profile'] = user_info
            # Also clear transfer logs
            cfg['transfer_log'] = {}
            pilot.config.config.save(cfg)

    def load_option(self, option):
        return self.load_user_info().get(option)

    def save_option(self, option, value):
        cfg = pilot.config.config.load()
        cfg['profile'][option] = value
        pilot.config.config.save(cfg)

    @property
    def name(self):
        return self.load_option('name') or ''

    @name.setter
    def name(self, value):
        self.save_option('name', value)

    @property
    def organization(self):
        return self.load_option('organization') or ''

    @organization.setter
    def organization(self, value):
        self.save_option('organization', value)


profile = Profile()

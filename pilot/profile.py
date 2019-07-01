from pilot import config


class Profile(config.ConfigSection):

    SECTION = 'profile'

    def load_user_info(self):
        return self.config.load()['profile']

    def save_user_info(self, user_info):
        old_info = self.load_user_info()
        if user_info['sub'] != old_info.get('sub'):
            cfg = self.config.load()
            cfg['profile'] = user_info
            # Also clear transfer logs
            self.config.save(cfg)

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

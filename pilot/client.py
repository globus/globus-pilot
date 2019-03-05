from globus_sdk import AuthClient
from fair_research_login import (NativeClient, LoadError)
from pilot.config import config


class PilotClient(NativeClient):

    DEFAULT_SCOPES = ['profile', 'openid']
    CLIENT_ID = 'e4d82438-00df-4dbd-ab90-b6258933c335'

    def __init__(self):
        super().__init__(client_id=self.CLIENT_ID,
                         token_storage=config,
                         default_scopes=self.DEFAULT_SCOPES)

    def login(self, *args, **kwargs):
        super().login(*args, **kwargs)
        if not config.get_user_info():
            ac_authorizer = self.get_authorizers()['auth.globus.org']
            auth_cli = AuthClient(authorizer=ac_authorizer)
            user_info = auth_cli.oauth2_userinfo()
            config.save_user_info(user_info.data)

    def logout(self):
        super().logout()
        config.clear()

    def is_logged_in(self):
        try:
            self.load_tokens()
            return True
        except LoadError:
            return False

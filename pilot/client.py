import os
import time
import requests
import globus_sdk
from globus_sdk import AuthClient, SearchClient
from fair_research_login import (NativeClient, LoadError)
from pilot.config import config


class PilotClient(NativeClient):

    DEFAULT_SCOPES = [
        'profile',
        'openid',
        'urn:globus:auth:scope:search.api.globus.org:all',
        'https://auth.globus.org/scopes/'
            '56ceac29-e98a-440a-a594-b41e7a084b62/all',
    ]
    CLIENT_ID = 'e4d82438-00df-4dbd-ab90-b6258933c335'
    SEARCH_INDEX = '889729e8-d101-417d-9817-fa9d964fdbc9'
    APP_NAME = 'NCI Pilot 1 Dataframe Manager'
    ENDPOINT = 'ebf55996-33bf-11e9-9fa4-0a06afd4a22e'
    BASE_DIR = '/restricted/dataframes'
    TESTING_DIR = '/restricted/dataframes/cli_testing'
    SEARCH_INDEX_TEST = 'e0849c9b-b709-46f3-be21-80893fc1db84'
    GROUP = 'd99b3400-33e7-11e9-8857-0af4690c7c7e'
    
    def __init__(self):
        super().__init__(client_id=self.CLIENT_ID,
                         token_storage=config,
                         default_scopes=self.DEFAULT_SCOPES,
                             app_name=self.APP_NAME)

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

    @property
    def gsearch(self):
        authorizer = self.get_authorizers()['search.api.globus.org']
        return SearchClient(authorizer=authorizer)

    def get_index(self, testing=False):
        return self.SEARCH_INDEX_TEST if testing else self.SEARCH_INDEX

    def get_dataframe_url(self, dataframe, directory, testing=False):
        if testing:
            directory = self.TESTING_DIR
        return 'https://{}.e.globus.org{}/{}'.format(
            self.ENDPOINT, directory, dataframe
        )

    def get_subject(self, dataframe, directory, testing=False):
        if testing:
            return 'globus://{}{}/{}'.format(self.ENDPOINT, self.TESTING_DIR,
                                             dataframe)
        path = os.path.join(self.BASE_DIR, directory, dataframe)
        return 'globus://{}{}'.format(self.ENDPOINT, path)

    def get_search_entry(self, basename, directory, testing=False):
        try:
            entry = self.gsearch.get_subject(
                self.get_index(testing),
                self.get_subject(basename, directory, testing))
            return entry['content'][0]
        except globus_sdk.exc.SearchAPIError:
            return None

    def ingest_entry(self, gmeta_entry, testing=False):
        sc = self.gsearch
        result = sc.ingest(self.get_index(testing), gmeta_entry)
        time.sleep(2)
        if sc.get_task(result['task_id'])['state'] != 'SUCCESS':
            # sc.delete_entry(self.SEARCH_INDEX_TEST, subject)
            raise Exception('Failed to ingest search subject')
        return True

    def upload(self, dataframe, destination, testing=False):
        petrel = self.load_tokens()['petrel.https.server']['access_token']
        headers = {'Authorization': 'Bearer {}'.format(petrel)}

        filename = os.path.basename(dataframe)
        url = self.get_dataframe_url(filename, destination, testing)

        with open(dataframe, 'rb') as fh:
            # Get the user info as JSON
            resp = requests.put(
                url, headers=headers, data=fh, allow_redirects=False)
            return resp.status_code

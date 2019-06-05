from pilot.profile import Profile


MOCK_PROFILE = {
    'name': 'Rosalind Franklin',
    'preferred_username': 'franklinr@globusid.org',
    'organization': 'The French Government Central Laboratory',
    'identity_provider': '41143743-f3c8-4d60-bbdb-eeecaba85bd9',
    'identity_provider_display_name': 'Globus ID',
    'sub': '102e192b-5acb-47ee-80c7-e613d86e7d6a',


}


def test_save_user_info(mock_config):
    profile = Profile()
    profile.save_user_info(MOCK_PROFILE)
    assert profile.load_user_info() == MOCK_PROFILE

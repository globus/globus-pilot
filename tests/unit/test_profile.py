from pilot import profile
from tests.unit.mocks import MOCK_PROFILE


def test_save_user_info(mock_config):
    pfile = profile.Profile(mock_config)
    assert pfile.load_user_info() == {}
    pfile.save_user_info(MOCK_PROFILE)
    assert pfile.load_user_info() == MOCK_PROFILE


def test_profile_getter_setters(mock_config):
    pfile = profile.Profile(mock_config)
    assert pfile.load_user_info() == {}
    pfile.save_user_info(MOCK_PROFILE)
    assert pfile.organization == 'The French Government Central Laboratory'
    assert pfile.name == 'Rosalind Franklin'

    pfile.organization = 'Another Laboratory'
    assert pfile.organization == 'Another Laboratory'
    pfile.name = 'Person'
    assert pfile.name == 'Person'

import pilot
from tests.unit.mocks import MOCK_PROFILE


def test_save_user_info(mock_profile):
    assert pilot.profile.profile.load_user_info() == MOCK_PROFILE

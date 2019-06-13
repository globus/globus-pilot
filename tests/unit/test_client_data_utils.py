import pytest
from pilot.client import PilotClient


@pytest.mark.skip
def test_upload_gcp(mock_transfer_client, simple_tsv, mock_config):
    pc = PilotClient()
    result = pc.upload_gcp(simple_tsv, 'bar', test=True)
    assert result.data['code'] == 'Accepted'

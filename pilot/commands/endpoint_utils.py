import logging
import globus_sdk
import pilot.commands
import pilot.exc

log = logging.getLogger(__name__)


def test_local_endpoint():
    pc = pilot.commands.get_pilot_client()
    tc = pc.get_transfer_client()
    try:
        tc.operation_ls(pc.profile.load_option('local_endpoint'))
    except globus_sdk.exc.TransferAPIError as tapie:
        log.exception(tapie)
        raise pilot.exc.LocalEndpointUnresponsive(fmt=[tapie.message])

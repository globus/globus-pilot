from pilot.client import PilotClient
from pilot import logging_cfg


def get_pilot_client():
    logging_cfg.setup_logging(level='CRITICAL')
    return PilotClient()

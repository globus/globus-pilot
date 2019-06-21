import os
import logging.config


def setup_logging(level=None):
    """
    Original source: Globus CLI
    https://github.com/globus/globus-cli/blob/master/globus_cli/config.py
    Setup global logging for this project. the PILOT_LOGGING env var can be set
    to override defaults within the CLI or SDK. Otherwise, by default, the SDK
    will use 'ERROR' and the CLI will use 'CRITICAL'
    """
    level = os.getenv('PILOT_LOGGING', level or 'ERROR')
    logging.config.dictConfig({
        'version': 1,
        'formatters': {
            'basic': {'format': '[%(levelname)s] '
                                '%(name)s::%(funcName)s() %(message)s'}
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': level,
                'formatter': 'basic',
            }
        },
        'loggers': {'pilot': {'level': level, 'handlers': ['console']}},
    })

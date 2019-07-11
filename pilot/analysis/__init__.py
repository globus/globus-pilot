import logging
import sys
from pilot import exc
from pilot.analysis import tsv

log = logging.getLogger(__name__)

ANALYZE_MAP = {
    'text/tab-separated-values': tsv.analyze_tsv,
    'text/csv': tsv.analyze_csv,
}


def analyze_dataframe(filename, mimetype=None, foreign_keys=None):
    analyze_function = ANALYZE_MAP.get(mimetype, None)
    if analyze_function is None:
        log.debug('No analyzer for mimetype {}'.format(mimetype))
        return {}
    try:
        return analyze_function(filename, foreign_keys=foreign_keys)
    except Exception as e:
        log.exception(e)
        log.error('Failed to parse metadata.')
        msg = 'Failed to analyze {}'.format(filename)
        raise exc.AnalysisException(msg, sys.exc_info()) from None

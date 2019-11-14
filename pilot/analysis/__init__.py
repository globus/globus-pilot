import logging
import sys
from pilot import exc
from pilot.analysis import mimetypes, pandas as pandalyze

log = logging.getLogger(__name__)

ANALYZE_MAP = {
    'text/tab-separated-values': pandalyze.analyze_tsv,
    'text/csv': pandalyze.analyze_csv,
    'application/x-hdf': pandalyze.analyze_hdf,
    'application/x-parquet': pandalyze.analyze_parquet,
    'application/x-feather': pandalyze.analyze_feather,
}


def analyze_dataframe(filename, mimetype=None):
    mimetype = mimetype or mimetypes.detect_type(filename)
    analyze_function = ANALYZE_MAP.get(mimetype)
    if analyze_function is None:
        log.debug('No analyzer for mimetype {}'.format(mimetype))
        return {}
    try:
        return analyze_function(filename)
    except Exception as e:
        log.exception(e)
        log.error('Failed to parse metadata.')
        msg = 'Failed to analyze {}'.format(filename)
        raise exc.AnalysisException(msg, sys.exc_info()) from None

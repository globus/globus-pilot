import logging
import sys
from pilot import exc
from pilot.analysis import mimetypes

log = logging.getLogger(__name__)


try:
    from pilot.analysis import pandas as pandalyze
    pandas_map = {
        'text/tab-separated-values': pandalyze.analyze_tsv,
        'text/csv': pandalyze.analyze_csv,
        'application/x-hdf': pandalyze.analyze_hdf,
        'application/x-parquet': pandalyze.analyze_parquet,
        'application/x-feather': pandalyze.analyze_feather,
    }
except ImportError:
    log.debug('Dependency not found, pandas analysis disabled',
              exc_info=True)
    pandas_map = {}

try:
    from pilot.analysis import image as imaginalyze
    image_map = {
        'image/jpeg': imaginalyze.analyze_image,
        'image/png': imaginalyze.analyze_image,
    }
except ImportError:
    log.debug('Dependency not found, imaging analysis disabled',
              exec_info=True)
    image_map = {}


ANALYZE_MAP = {}
ANALYZE_MAP.update(pandas_map)
ANALYZE_MAP.update(image_map)


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

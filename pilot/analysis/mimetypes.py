import logging
import mimetypes
import puremagic
try:
    import pandas as pd
except ImportError:
    pd = None

log = logging.getLogger(__name__)


def detect_type(url, functions=None):
    """This function mimics mimetypes.guess_type, but attempts to open the
    file and read data to determine what the type is."""
    for guesser, name in functions or MIMETYPE_DETECTORS:
        try:
            guess = guesser(url)
            if guess and any(guess):
                log.debug('Determined mimetype to be {}'.format(name))
                return guess
        except Exception:
            log.debug('Attempt to guess mimetype with {} failed'.format(name))


def general_mimetype(url):
    mt, _ = mimetypes.guess_type(url, strict=True)
    return mt


def puremagic_mimetype(url):
    return puremagic.magic_file(url)[0].mime_type


def detect_parquet(url):
    if not pd.read_parquet(url).empty:
        return 'application/x-parquet'


def detect_feather(url):
    if not pd.read_feather(url).empty:
        return 'application/x-feather'


def detect_hdf(url):
    store = pd.HDFStore(url, 'r')
    keys = store.keys()
    store.close()
    if len(keys) > 0:
        return 'application/x-hdf'


def detect_delimiter_separated_values(filename):
    """Attempts to check for csv or tsv mimetypes"""
    df = pd.read_csv(filename)
    if len(df.columns) > 1:
        return 'text/csv'
    if len(df.columns) == 1:
        if df.columns[0].count('\t') >= 1:
            return 'text/tab-separated-values'


def get_text_or_binary(filename):
    """Read the first 1024 and attempt to decode it in utf-8. If this succeeds,
    the file is determined to be text. If not, its binary."""
    with open(filename, 'rb') as f:
        chunk = f.read(1024)
    try:
        chunk.decode('utf-8')
        return 'text/plain'
    except UnicodeDecodeError:
        return 'application/octet-stream'


MIMETYPE_DETECTORS = [
    (general_mimetype, []),
    (puremagic_mimetype, []),
    (detect_parquet, ['application/x-parquet']),
    (detect_feather, ['application/x-feather']),
    (detect_hdf, ['application/x-hdf']),
    (detect_delimiter_separated_values, ['text/csv',
                                         'text/tab-separated-values']),
    (get_text_or_binary, ['text/plain', 'application/octet-stream']),
]

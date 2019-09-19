import pytest
from pilot.analysis.mimetypes import (
    detect_type, detect_parquet, detect_feather, detect_hdf,
    detect_delimiter_separated_values, get_text_or_binary
)

from tests.unit.mocks import ANALYSIS_MIXED_FILES, ANALYSIS_BLIND_FILES

# Analyzers that test for specific mimetypes. Don't bother testing the general
# detectors.
SPECIFIC_DETECTORS = [
    (detect_parquet, ['application/x-parquet']),
    (detect_feather, ['application/x-feather']),
    (detect_hdf, ['application/x-hdf']),
    (detect_delimiter_separated_values, ['text/csv',
                                         'text/tab-separated-values']),
]
ALL_MIMETYPE_FILES = ANALYSIS_MIXED_FILES + ANALYSIS_BLIND_FILES


@pytest.mark.parametrize("filename,mimetype", ANALYSIS_MIXED_FILES)
def test_postulate_type(filename, mimetype):
    assert detect_type(filename) == mimetype


@pytest.mark.parametrize("filename,mimetype", ANALYSIS_BLIND_FILES)
def test_postulate_type_without_extensions(filename, mimetype):
    skip = []
    if mimetype not in skip:
        assert detect_type(filename) == mimetype


@pytest.mark.parametrize("function,mimetypes", SPECIFIC_DETECTORS)
def test_mimetype_analyzers_against_all_types(function, mimetypes):
    all_types = ANALYSIS_MIXED_FILES + ANALYSIS_BLIND_FILES
    for filename, mimetype in all_types:
        try:
            detected_type = function(filename)
            if detected_type:
                assert detected_type in mimetypes
                assert detected_type == mimetype
            else:
                assert detected_type not in mimetypes
        except AssertionError:
            raise
        except Exception:
            # It's ok if the individual detectors raise errors. Raising errors
            # is another way to say the type could not be determined, and
            # individual detectors should never be run outside 'postulate_type'
            pass


def test_text_or_binary():
    for filename, mimetype in ALL_MIMETYPE_FILES:
        print(filename)
        if mimetype.startswith('text'):
            print((filename, mimetype))
            assert get_text_or_binary(filename) == 'text/plain'
        else:
            assert get_text_or_binary(filename) == 'application/octet-stream'
        print('{} Success'.format(mimetype))

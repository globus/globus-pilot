import pytest
import pandas
from io import StringIO
from pilot.analysis import analyze_dataframe
from pilot import exc

from tests.unit.mocks import ANALYSIS_MIXED_FILES


@pytest.mark.parametrize("filename,mimetype", ANALYSIS_MIXED_FILES)
def test_eval(filename, mimetype):
    ana = analyze_dataframe(filename, mimetype)
    assert ana['numcols'] == 2
    assert ana['numrows'] == 99
    row1_keys = set(ana['field_definitions'][0].keys())
    row2_keys = set(ana['field_definitions'][0].keys())
    label_set = set(ana['labels'].keys())
    assert row1_keys.issubset(label_set)
    assert row2_keys.issubset(label_set)
    # The combination of rows 1 and 2 should contain all the labels
    rows_union = row1_keys.union(row2_keys)
    assert not rows_union.isdisjoint(label_set)


def test_preview_bytes(mixed_tsv):
    ana = analyze_dataframe(mixed_tsv, 'text/tab-separated-values')
    with open(mixed_tsv) as fp:
        preview_data = StringIO(fp.read(ana['previewbytes']))
    preview_df = pandas.read_csv(preview_data, sep='\t', encoding='utf8')
    normal_df = pandas.read_csv(mixed_tsv, sep='\t')

    assert list(preview_df.columns) == list(normal_df.columns)
    assert preview_df.head(10).to_dict() == normal_df.head(10).to_dict()
    assert preview_df.head(11).to_dict() != normal_df.head(11).to_dict()


def test_analyze_dataframe_with_unknown_mimetype(mixed_tsv):
    assert analyze_dataframe(mixed_tsv, 'completely_unknown_mimetype') == {}


def test_analyze_unexpected_error():
    with pytest.raises(exc.AnalysisException):
        analyze_dataframe('does-not-exist', 'text/csv')

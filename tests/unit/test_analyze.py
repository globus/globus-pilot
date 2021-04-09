import pytest
import pandas
from io import StringIO
from pilot.analysis import analyze_dataframe
from pilot import exc

from tests.unit.mocks import ANALYSIS_MIXED_FILES

ANALYZABLE_MIMETYPES = [
    'text/csv', 'text/tab-separated-values',
    'application/x-feather', 'application/x-parquet', 'application/x-hdf'
]

EXPECTED_MIXED_ANALYSIS_RESULT = {
    'field_definitions': [
        {'25': 25.5,
         '50': 50.0,
         '75': 74.5,
         'count': 99,
         # Tableschema field, only visible in tsvs, csvs
         # 'format': 'default',
         'max': 99.0,
         'mean': 50.0,
         'min': 1.0,
         'name': 'Numbers',
         'reference': None,
         'std': 28.722813232690143,
         'type': 'float64'},
        {'count': 99,
         # 'format': 'default',
         'frequency': 50,
         'name': 'Title',
         'reference': None,
         'top': 'baz',
         'type': 'string',
         'unique': 3}],
    'labels': {'25': '25th Percentile',
               '50': '50th Percentile',
               '75': '75th Percentile',
               'count': 'Number of non-null entries',
               'format': 'Format',
               'frequency': 'Frequency of Top Common Value',
               'max': 'Maximum Value',
               'mean': 'Mean Value',
               'min': 'Minimum Value',
               'name': 'Column Name',
               'reference': 'Link to resource definition',
               'std': 'Standard Deviation',
               'top': 'Top Common',
               'type': 'Data Type',
               'unique': 'Unique Values'},
    'name': 'Data Dictionary',
    'numcols': 2,
    'numrows': 99,
    # Only viewable in text-based files -- tsvs, csvs
    # 'previewbyptes': 75
}

EXTENDED_ANALYSIS_MIMETYPES = ['text/csv', 'text/tab-separated-values']

ANALYZABLE_MIXED_FILES = [(f, mtype) for f, mtype in ANALYSIS_MIXED_FILES
                          if mtype in ANALYZABLE_MIMETYPES]


@pytest.mark.skip
@pytest.mark.parametrize("filename,mimetype", ANALYZABLE_MIXED_FILES)
def test_analyze_filetypes(filename, mimetype):
    ana = analyze_dataframe(filename, mimetype)
    if mimetype == 'application/x-hdf':
        ana = ana[0]
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
    assert ana['labels'] == EXPECTED_MIXED_ANALYSIS_RESULT['labels']
    for result, expected in zip(
            ana['field_definitions'],
            EXPECTED_MIXED_ANALYSIS_RESULT['field_definitions']):
        from pprint import pprint
        pprint(result)
        for field in expected:
            assert result.get(field) == expected.get(field)

    # Check extended stuff
    if mimetype in EXTENDED_ANALYSIS_MIMETYPES:
        assert ana['previewbytes'] == 75
        for field in ana['field_definitions']:
            assert field['format'] == 'default'


@pytest.mark.skip
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


@pytest.mark.skip
def test_analyze_unexpected_error():
    with pytest.raises(exc.AnalysisException):
        analyze_dataframe('does-not-exist', 'text/csv')

import pandas
from pilot.analysis import analyze_dataframe
from io import StringIO

def test_analyze_dataframe(simple_tsv):
    ana = analyze_dataframe(simple_tsv)
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


def test_preview_bytes(simple_tsv):
    ana = analyze_dataframe(simple_tsv)
    with open(simple_tsv) as fp:
        preview_data = StringIO(fp.read(ana['previewbytes']))
    preview_df = pandas.read_csv(preview_data, sep='\t', encoding='utf8')
    normal_df = pandas.read_csv(simple_tsv, sep='\t')

    assert list(preview_df.columns) == list(normal_df.columns)
    assert preview_df.head(10).to_dict() == normal_df.head(10).to_dict()
    assert preview_df.head(11).to_dict() != normal_df.head(11).to_dict()

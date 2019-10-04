import os
from unittest.mock import Mock
from pilot import search_parse
from tests.unit.mocks import ANALYSIS_FILE_BASE_DIR

test_search_record = os.path.join(ANALYSIS_FILE_BASE_DIR, 'dataset',
                                  'valid-typical.json')


def test_parse_record(monkeypatch, mock_search_data):
    log = Mock()
    monkeypatch.setattr(search_parse, 'log', log)
    data = search_parse.parse_result(mock_search_data)
    for info in data:
        assert all(info)
    print(f'Exceptions when parsing: {log.exception.call_args}')
    assert not log.exception.called


def test_parse_field_metadata(monkeypatch, mock_search_data):
    log = Mock()
    monkeypatch.setattr(search_parse, 'log', log)
    meta = mock_search_data['files'][0]['field_metadata']
    field_meta = search_parse.get_field_metadata(meta)
    both = ['name', 'type', 'count']
    number = ['min', 'max', 'mean', 'std', '25', '50', '75']
    string = ['count', 'frequency', 'top', 'unique']
    for entry in field_meta:
        fields = dict(entry)
        assert all([fields[i] for i in both])
        if fields['type'] == 'string':
            assert all(fields[i] for i in string)
        elif fields['type'] == 'float64':
            assert all(fields[i] for i in number)
    print(f'Exceptions when parsing: {log.exception.call_args}')
    assert not log.exception.called

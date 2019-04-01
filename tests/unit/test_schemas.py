import os
import sys
import traceback
import pytest
import json
import jsonschema

from pilot.validation import get_schemas

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SCHEMA_FOLDER = os.path.join(BASE_DIR, 'tests', 'unit', 'files', 'schemas')

schemas = get_schemas()
schema_test = []
for name in schemas.keys():
    dir = os.path.join(SCHEMA_FOLDER, name)
    if not os.path.exists(dir):
        raise ValueError('No test folder {}'.format(dir))

    for filename in os.listdir(dir):
        if os.path.splitext(filename)[1] == '.json':
            schema_test.append((name, filename))


@pytest.mark.parametrize("name,schema", schemas.items())
def test_basic_validation(name, schema):
    resolver = jsonschema.RefResolver(base_uri="file://{}/".format(name),
                                      referrer=schema)
    validator = jsonschema.Draft4Validator(
        jsonschema.Draft4Validator.META_SCHEMA,
        resolver=resolver)
    try:
        validator.validate(schema)
    except jsonschema.exceptions.ValidationError as ve:
        traceback.print_exc()
        print('Failed SCHEMA validation for "{}.json"'.format(name),
              file=sys.stderr)
        assert False



@pytest.mark.parametrize("schema_name,filename", schema_test)
def test_validate_sample_schemas(schema_name, filename):
    fpath = os.path.join(SCHEMA_FOLDER, schema_name, filename)
    with open(fpath) as fh:
        instance = json.load(fh)

    if filename.startswith('valid'):
        jsonschema.validate(schema=schemas.get(schema_name),
                            instance=instance)
    elif filename.startswith('invalid'):
        with pytest.raises(jsonschema.exceptions.ValidationError):
            jsonschema.validate(schema=schemas.get(schema_name),
                                instance=instance)
    else:
        raise ValueError('Schema test {}:{} must be prefixed with valid or '
                         'invalid'.format(schema_name, filename))
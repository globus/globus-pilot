"""
README!

Tests are automatic! Drop files into the correct directory and new schemas will
automatically be added as a new test.

To add new schemas, drop them into the pilot/schemas directory.
To add tests for new schemas, drop them into the
tests/unit/files/schemas/<schema-name>/ directory.

Schema test names starting with 'valid' should validate, 'invalid' should
raise a validation error.
"""
import os
import sys
import traceback
import pytest
import json
import jsonschema

from pilot.validation import get_schemas, BASE_SCHEMA_DIR

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SCHEMA_TEST_FOLDER = os.path.join(BASE_DIR, 'tests', 'unit', 'files',
                                  'schemas')

schemas = get_schemas()
schema_test = []
for name in schemas.keys():
    dir = os.path.join(SCHEMA_TEST_FOLDER, name)
    if not os.path.exists(dir):
        raise ValueError('No test folder {}'.format(dir))

    for filename in os.listdir(dir):
        if os.path.splitext(filename)[1] == '.json':
            schema_test.append((name, filename))


@pytest.mark.parametrize("name,schema", schemas.items())
def test_basic_validation(name, schema):
    if name == 'dc':
        return
    resolver = jsonschema.RefResolver(
        base_uri="file://{}".format(BASE_SCHEMA_DIR),
        referrer=name
    )
    validator = jsonschema.Draft4Validator(
        jsonschema.Draft4Validator.META_SCHEMA,
        resolver=resolver)
    try:
        validator.validate(schema)
    except jsonschema.exceptions.ValidationError:
        traceback.print_exc()
        print('Failed SCHEMA validation for "{}.json"'.format(name),
              file=sys.stderr)
        assert False


@pytest.mark.parametrize("schema_name,filename", schema_test)
def test_validate_sample_schemas(schema_name, filename):
    fpath = os.path.join(SCHEMA_TEST_FOLDER, schema_name, filename)
    schema_path = os.path.join(BASE_SCHEMA_DIR, schema_name)
    # datacite has special refs, we don't want to include
    if schema_name != 'dc':
        resolver = jsonschema.RefResolver(
            base_uri="file://{}".format(schema_path),
            referrer=schema_name
        )
    else:
        resolver = None
    with open(fpath) as fh:
        instance = json.load(fh)

    if filename.startswith('valid'):
        jsonschema.validate(schema=schemas.get(schema_name),
                            instance=instance,
                            resolver=resolver)
    elif filename.startswith('invalid'):
        with pytest.raises(jsonschema.exceptions.ValidationError):
            jsonschema.validate(schema=schemas.get(schema_name),
                                instance=instance,
                                resolver=resolver)
    else:
        raise ValueError('Schema test {}:{} must be prefixed with valid or '
                         'invalid'.format(schema_name, filename))

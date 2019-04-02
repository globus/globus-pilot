import os
import json
import jsonschema

BASE_DIR = os.path.dirname(__file__)
BASE_SCHEMA_DIR = os.path.join(BASE_DIR, 'schemas')


def get_schemas():
    schemas = {}
    files = [f for f in os.listdir(BASE_SCHEMA_DIR)
             if os.path.splitext(f)[1] == '.json']

    for f in files:
        fname = os.path.join(BASE_SCHEMA_DIR, f)
        with open(fname) as fh:
            sname, _ = os.path.splitext(f)
            try:
                schemas[sname] = json.load(fh)
            except json.decoder.JSONDecodeError:
                raise Exception('Error loading {}'.format(fname))
    return schemas


def validate_ingest_doc(gmeta_json):
    schema = get_schemas()['globus_search_gmeta_record']
    jsonschema.validate(schema=schema, instance=gmeta_json)

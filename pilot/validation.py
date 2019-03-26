import jsonschema
from pilot.schemas import get_schemas

def validate_ingest_doc(gmeta_json):
    schema = get_schemas()['globus_search_gmeta_record']
    jsonschema.validate(schema=schema, instance=gmeta_json)

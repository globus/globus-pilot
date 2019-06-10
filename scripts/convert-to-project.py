#!/usr/bin/env python

# argv[1] old gmeta file
# argv[2] directory for new file
# load old file
# update subject
# generate file name for new gmeta file
# update file manifest with new location
# update name of project metadata
# ??
# validate

import os
import sys
import pprint
import json

import jsonschema

from pilot.validation import get_schemas, BASE_SCHEMA_DIR
schemas = get_schemas()

schema_name = 'dataset'

old_gmeta_fname = sys.argv[1]
output_dir = sys.argv[2]

with open(old_gmeta_fname) as f:
    gmeta = json.loads(f.read())

print(gmeta['subject'])
new_subject = gmeta['subject'].replace('restricted', 'projects/NCI-Pilot1')
print(new_subject)
new_gmeta_fname = output_dir + '/' + new_subject.lstrip('globus://ebf55996-33bf-11e9-9fa4-0a06afd4a22e/').replace('/','-') + '.gmeta'

new_metadata = gmeta['content'][0]
new_metadata['files'][0]['url'] = new_metadata['files'][0]['url'].replace('restricted', 'projects/NCI-Pilot1')

# remove data_type from files
try:
    new_metadata['files'][0].pop('data_type')
except:
    pass

# move ncipilot1 to project_metadata
new_metadata['project_metadata'] = new_metadata.pop('ncipilot')
new_metadata['project_metadata']['project-slug'] = 'ncipilot1'
new_metadata['files'][0]['field_metadata'] = new_metadata.pop('field_metadata')

# pprint.pprint(gmeta)
schema_path = os.path.join(BASE_SCHEMA_DIR, schema_name)
resolver = jsonschema.RefResolver(
    base_uri="file://{}".format(schema_path),
    referrer = schema_name
    )
jsonschema.validate(schema=schemas.get(schema_name),
                        instance=new_metadata,
                        resolver=resolver)

# pprint.pprint(new_metadata)

new_gmeta = {
    'ingest_type': 'GMetaEntry',
    'ingest_data': {
        'subject': new_subject,
        'visible_to': ['urn:globus:groups:id:d99b3400-33e7-11e9-8857-0af4690c7c7e'],
        'content': new_metadata
        }
    }

# pprint.pprint(new_gmeta)
with open(new_gmeta_fname, 'w') as f:
    f.write(json.dumps(new_gmeta))

import os
import json

BASE_DIR = os.path.dirname(__file__)

def get_schemas():
    schemas = {}
    files = [f for f in os.listdir(BASE_DIR)
             if os.path.splitext(f)[1] == '.json' ]

    for f in files:
        with open(os.path.join(BASE_DIR, f)) as fh:
            sname, _ = os.path.splitext(f)
            schemas[sname] = json.load(fh)
    return schemas

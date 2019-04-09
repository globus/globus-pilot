#!/usr/bin/env python

# add mimetype option
# remove search-test option
# json output for list and description
# pilot upload status (last n option)
# make json metadata required
# fix list fields showing up as Err

# bold header in field metadata
# add field stats to describe command in pilot

import sys
import json
import pandas
import numpy
from tableschema import infer, Schema

FOREIGN_KEYS = {
    "DRUG_ID": {
        "fields": ["DRUG_ID"],
        "reference": {
            "resource": "globus://ebf55996-33bf-11e9-9fa4-0a06afd4a22e:/restricted/dataframes/metadata/drugs",
            "fields": "ID"
            }
        },
        "CELLNAME": {
            "fields": ["CELLNAME"],
            "reference": {
                "resource": "globus://ebf55996-33bf-11e9-9fa4-0a06afd4a22e:/restricted/dataframes/metadata/celllines",
                "fields": "sample_name"
                }
            },
        "Sample": {
            "fields": ["Sample"],
            "reference": {
                "resource": "globus://ebf55996-33bf-11e9-9fa4-0a06afd4a22e:/restricted/dataframes/metadata/celllines",
                "fields": "sample_name"
                }
            }
    }


# create link to download tsv of column metadata

# also for rna seq
# https://ebf55996-33bf-11e9-9fa4-0a06afd4a22e.e.globus.org/restricted/dataframes/rna-seq/combined_rnaseq_data_combat

# 10x10 preview

def get_preview_byte_count(fileptr, num_rows=11):
    byte_cnt = 0
    preview_rows = [next(fileptr) for x in range(num_rows)]
    for row in preview_rows:
        byte_cnt += len(row)

    return byte_cnt

def get_pandas_inference(fileptr):
    df = pandas.read_csv(fileptr, sep='\t')
    col_info = df.describe(include='all')

    return col_info, df.shape[0], df.shape[1]

def get_schema_dict(filename):
    try:
        s = Schema(infer(filename))
    except:
        return None

    # work with schema in dict form
    s_dict = s.descriptor
    s_dict['foreignKeys'] = []
    for d in s_dict['fields']:
        if d['name'] in FOREIGN_KEYS.keys():
            s_dict['foreignKeys'].append(FOREIGN_KEYS[d['name']])
    return s_dict

def describe_dataframe(filename):
    schema_dict = get_schema_dict(filename)
    if schema_dict:
        fptr = open(filename)
        schema_dict['previewbytes'] = get_preview_byte_count(fptr)
        fptr.seek(0)
        pandas_col_metadata, nrows, ncols = get_pandas_inference(fptr)

        for d in schema_dict['fields']:
            c = pandas_col_metadata.get(d['name'])
            d['count'] = int(c['count'])
            if d['type'] == 'string':
                if not numpy.isnan(c['unique']):
                    d['unique'] = int(c['unique'])
                d['top'] = c['top']
                if not numpy.isnan(c['freq']):
                    d['frequency'] = int(c['freq'])
            else:
                d['type'] = str(c.dtype)
                for k in ("25", "50", "75"):
                    d[k] = float(c[k+'%'])
                for k in ('mean', "std", "min", "max"):
                    d[k] = float(c[k])

        schema_dict['field_definitions'] = schema_dict.pop('fields')
        schema_dict.update({
            "name": "Data Dictionary",
            "numrows": nrows,
            "numcols": ncols,
            "labels": {
                "name": "Column Name",
                "type": "Data Type",
                "format": "Format",
                "description": "Description"
                }
            })

        print(json.dumps(schema_dict, indent=4))
        return schema_dict
    else:
        return None

if __name__ == '__main__':
    describe_dataframe(sys.argv[1])


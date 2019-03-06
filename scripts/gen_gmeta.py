#!/usr/bin/env python
import csv
import json

def main():
    data = {}
    with open('DataframeMetadataSheet1.tsv') as tsvfile:
        reader = csv.DictReader(tsvfile, dialect='excel-tab')
        for row in reader:
            data[row['LOCATION']] = {
                "subject": "globus://ebf55996-33bf-11e9-9fa4-0a06afd4a22e:/restricted/dataframes/" + row['LOCATION'],
                'title' : row['TITLE'],
                'filename': row['NAME'],
                'description': row['DESCRIPTION'],
                'data_type': row['DATA TYPE'],
                'dataframe_type': row['DATA FRAME TYPE'],
                'source': row['SOURCE']
                }

    with open('md5.txt') as f:
        for line in f:
            loc, md5 = line.split()
            if loc in data:
                data[loc]['md5'] = md5
    with open('sizes.txt') as f:
        for line in f:
            loc, size = line.split()
            if loc in data:
                data[loc]['length'] = size
    with open('sha256.txt') as f:
        for line in f:
            loc, sha256 = line.split()
            if loc in data:
                data[loc]['sha256'] = sha256
    with open('rows.txt') as f:
        for line in f:
            loc, rows = line.split()
            if loc in data:
                data[loc]['rows'] = rows
    with open('cols.txt') as f:
        for line in f:
            loc, cols = line.split()
            if loc in data:
                data[loc]['cols'] = cols

    with open('base-example.json') as f:
        gm_base_text = f.read()

    for subj in data:
        gmeta = json.loads(gm_base_text)
        gmeta['ingest_data']['subject'] = 'globus://ebf55996-33bf-11e9-9fa4-0a06afd4a22e:/restricted/dataframes/' + subj
        gmeta['ingest_data']['content']['dc']['descriptions'][0]['description'] = data[subj]['description']
        gmeta['ingest_data']['content']['dc']['titles'][0] = {'title': data[subj]['title']}
        gmeta['ingest_data']['content']["remote_file_manifest"] = {
                "sha256": data[subj]['sha256'],
                "filename": data[subj]['filename'],
                "url": 'globus://ebf55996-33bf-11e9-9fa4-0a06afd4a22e:/restricted/dataframes/' + subj,
                "md5": data[subj]['md5'],
                "length": int(data[subj]['length']),
                "mimetype": "text/tab-separated-values" 
            }
        gmeta['ingest_data']['content']["ncipilot"] = {
            "numrows": int(data[subj]['rows']),
            "numcols": int(data[subj]['cols']),
            "data_type": data[subj]["data_type"],
            "dataframe_type": data[subj]["dataframe_type"]
            }
        if data[subj]['source']:
            srcs = data[subj]["source"].split(',')
            gmeta['ingest_data']['content']["ncipilot"]['source'] = []
            for src in srcs:
                gmeta['ingest_data']['content']["ncipilot"]['source'].append(src.strip())
        with open(subj+'.gmeta', 'w') as f:
            f.write(json.dumps(gmeta, indent=4, sort_keys=True))

if __name__ == '__main__':
    main()

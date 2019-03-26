import os
import hashlib

from pilot.client import PilotClient
from pilot.config import config

DEFAULT_HASH_ALGORITHMS = ['sha256', 'md5']
DEFAULT_CREATOR_AFFILIATIONS = ['Argonne National Laboratory']

GMETA_LIST = {
    "@version": "2016-11-09",
    "ingest_type": "GMetaList",
    "ingest_data": {
        "@version": "2016-11-09",
        "gmeta": []
    }
}

GMETA_ENTRY = {
    "@version": "2016-11-09",
    "visible_to": [],
    "content": '',
    "subject": ''
}

GROUP_URN_PREFIX = 'urn:globus:groups:id:{}'

def gen_gmeta(subject, visible_to, data):
    entry = GMETA_ENTRY.copy()
    entry['visible_to'] = [GROUP_URN_PREFIX.format(visible_to)]
    entry['subject'] = subject
    entry['content'] = data
    gmeta = GMETA_LIST.copy()
    gmeta['ingest_data']['gmeta'].append(entry)
    return gmeta

def gen_dc_metadata():
    name = config.get_user_info()['name']
    creator_name = ', '.join(name.split().reverse())
    creators = [{

    }]
    from pprint import pprint
    pprint(user_info)
    {
            "creators": [
                {
                    "affiliations": [
                        "Argonne National Laboratory"
                    ],
                    "creatorName": "Shukla, Maulik",
                    "familyName": "Shukla",
                    "givenName": "Maulik"
                },
                {
                    "affiliations": [
                        "Argonne National Laboratory"
                    ],
                    "creatorName": "Brettin, Thomas",
                    "familyName": "Brettin",
                    "givenName": "Thomas"
                },
                {
                    "affiliations": [
                        "Argonne National Laboratory"
                    ],
                    "creatorName": "Yoo, Hyunseung",
                    "familyName": "Yoo",
                    "givenName": "Hyunseung"
                }
            ],
            "dates": [
                {
                    "date": "2019-03-05T17:04:10.315060Z",
                    "dateType": "Created"
                },
                {
                    "date": "2019-03-05T17:04:10.315060Z",
                    "dateType": "Updated"
                }
            ],
            "descriptions": [
                {
                    "description": "Rescaled combined drug response data frame, which combines single drug response data from multiple sources, such as NCI60, SCL, SCLC, CCLE, GDSC, CTRP, and gCSI. The dose response values are linearly rescaled and/or clamped to be >= -100 and <= 300.",
                    "descriptionType": "Other"
                }
            ],
            "formats": [
                "text/tab-separated-values"
            ],
            "publicationYear": "2019",
            "publisher": "Argonne National Laboratory",
            "resourceType": {
                "resourceType": "Dataset",
                "resourceTypeGeneral": "Dataset"
            },
            "subjects": [
                {
                    "subject": "machine learning"
                },
                {
                    "subject": "genomics"
                }
            ],
            "titles": [
                {
                    "title": "Combined Dose Response - Rescaled"
                }
            ],
            "version": "1"
        }


def gen_remote_file_manifest(filepath, url, metadata={},
                             algorithms=DEFAULT_HASH_ALGORITHMS):
    rfm = metadata.copy()
    rfm.update({alg: compute_checksum(filepath, getattr(hashlib, alg)())
                for alg in algorithms})
    rfm.update({
        'filename': os.path.basename(filepath),
        'url': url,
        'length': os.stat(filepath).st_size
    })
    return [rfm]


def compute_checksum(file_path, algorithm, block_size=65536):
    if not algorithm:
        algorithm = hashlib.sha256()
    with open(os.path.abspath(file_path), 'rb') as open_file:
        buf = open_file.read(block_size)
        while len(buf) > 0:
            algorithm.update(buf)
            buf = open_file.read(block_size)
    open_file.close()
    return algorithm.hexdigest()

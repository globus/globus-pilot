import json


class PilotClientException(Exception):
    pass


class RequiredUploadFields(PilotClientException):

    def __init__(self, fields, *args, **kwargs):
        self.fields = fields

    def __str__(self):
        example = {f: '<VALUE>' for f in self.fields}
        return ('Please provide the following fields in a JSON file with the '
                '-j flag:\n {}'.format(json.dumps(example, indent=4)))

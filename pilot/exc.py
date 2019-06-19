import json
from globus_sdk.exc import GlobusAPIError


class PilotClientException(Exception):
    pass


class PilotInvalidProject(PilotClientException):
    pass


class PilotValidator(PilotClientException):

    def __init__(self, message, *args, **kwargs):
        super().__init__()
        self.message = message or 'Error Validating Input'

    def __str__(self):
        return self.message


class RequiredUploadFields(PilotClientException):

    def __init__(self, message, fields, *args, **kwargs):
        self.message = message
        self.fields = fields

    def __str__(self):
        example = {f: '<VALUE>' for f in self.fields}
        return ('{}. Please provide minimum fields with the -j flag. Example:'
                '\n {}'.format(self.message, json.dumps(example, indent=4)))


class HTTPSClientException(PilotClientException, GlobusAPIError):
    pass

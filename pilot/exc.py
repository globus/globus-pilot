import json
from globus_sdk.exc import GlobusAPIError
from enum import IntEnum


class ExitCodes(IntEnum):
    SUCCESS = 0
    UNCAUGHT_EXCEPTION = 1
    NOT_LOGGED_IN = 2
    NO_DESTINATION_PROVIDED = 3
    DIRECTORY_DOES_NOT_EXIST = 4
    GLOBUS_TRANSFER_ERROR = 5
    INVALID_METADATA = 6
    RECORD_EXISTS = 7
    INVALID_CLIENT_CONFIGURATION = 8
    NO_LOCAL_ENDPOINT_SET = 9


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


class InvalidField(PilotClientException):
    pass


class AnalysisException(PilotClientException):
    def __init__(self, message, exc):
        super().__init__(message)
        self.message = message
        self.original_exc_info = exc


class HTTPSClientException(PilotClientException, GlobusAPIError):
    pass

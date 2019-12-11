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
    DESTINATION_IS_RECORD = 10
    NO_RECORD_EXISTS = 11


class PilotClientException(Exception):
    pass


class PilotContextException(Exception):
    pass


class PilotInvalidProject(PilotClientException):
    pass


class PilotValidator(PilotClientException):

    def __init__(self, message, *args, **kwargs):
        super().__init__()
        self.message = message or 'Error Validating Input'

    def __str__(self):
        return self.message


class RecordDoesNotExist(PilotClientException):
    pass


class PilotCodeException(PilotClientException):
    """Pilot Code Exceptions are a general class for any exception that might
    be thrown during the execution of a pilot command. The main difference from
    regular exceptions is a CODE, which must correspond to exc.ExitCodes, which
    is the integer which will be passed to sys.exit(). This is solely to
    facilitate bash scripting, so someone can check the exit code of a command
    and have enough context to make a decision with that information.

    Calling str(pce) on these exceptions must yield a user readable error,
    where repr(pce) might also yield the exit code.
    """
    MESSAGE = 'Unknown Error'
    CODE = ExitCodes.UNCAUGHT_EXCEPTION

    def __init__(self, message=None, fmt=None, verbose=False):
        super().__init__()
        self.message = message or self.MESSAGE
        self.fmt = fmt
        if fmt:
            self.message = self.message.format(*fmt)
        self.verbose = verbose
        self.verbose_output = ''

    def __str__(self):
        return '{}\n{}'.format(
            self.message, self.verbose_output if self.verbose else '')

    def __repr__(self):
        return '({}) {}\n{}'.format(
            self.CODE.name, self.message,
            self.verbose_output if self.verbose else '')


class NoDestinationProvided(PilotCodeException):
    MESSAGE = ('No Destination Provided. Please select one from the '
               'directory or "/" for root:\n{}')
    CODE = ExitCodes.NO_DESTINATION_PROVIDED


class DirectoryDoesNotExist(PilotCodeException):
    MESSAGE = 'Directory does not exist: "{}"'
    CODE = ExitCodes.DIRECTORY_DOES_NOT_EXIST


class GlobusTransferError(PilotCodeException):
    MESSAGE = '{}'
    CODE = ExitCodes.GLOBUS_TRANSFER_ERROR


class NoChangesNeeded(PilotCodeException):
    MESSAGE = '"{}": Files and search entry are an exact match.'
    CODE = ExitCodes.SUCCESS


class DestinationIsRecord(PilotCodeException):
    MESSAGE = ('The Destination "{}" is a record. Adding records to existing '
               'collections is not supported.')
    CODE = ExitCodes.DESTINATION_IS_RECORD


class RecordExists(PilotCodeException):
    MESSAGE = '"{}": Record Exists, extra confirmation needed to overwrite.'
    CODE = ExitCodes.RECORD_EXISTS

    def __init__(self, previous_metadata, fmt=None, verbose=False):
        super().__init__(verbose=verbose, fmt=fmt)
        self.previous_metadata = previous_metadata


class DryRun(PilotCodeException):
    MESSAGE = 'Success! (Dry Run -- No changes applied.)'
    CODE = ExitCodes.SUCCESS

    def __init__(self, stats=None, verbose=False):
        super().__init__(verbose=verbose)
        self.message = self.MESSAGE
        self.stats = stats
        self.previous_metadata = stats.get('previous_metadata')
        self.new_metadata = stats['new_metadata']
        self.verbose_output = self.stats, self.new_metadata


class NoLocalEndpointSet(PilotCodeException):
    MESSAGE = 'No Local endpoint set'
    CODE = ExitCodes.NO_LOCAL_ENDPOINT_SET


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

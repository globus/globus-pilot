from globus_sdk import AccessTokenAuthorizer, RefreshTokenAuthorizer
from globus_sdk.base import BaseClient
from pilot.exc import HTTPSClientException


class HTTPSClient(BaseClient):
    allowed_authorizer_types = (AccessTokenAuthorizer, RefreshTokenAuthorizer)

    error_class = HTTPSClientException

    def __init__(self, authorizer=None, base_url='', **kwargs):
        super().__init__(
            self, "http_client", base_url=base_url,
            authorizer=authorizer, **kwargs
        )

from globus_sdk import AccessTokenAuthorizer, RefreshTokenAuthorizer
from globus_sdk.base import BaseClient, slash_join
from pilot.exc import HTTPSClientException
from globus_sdk import exc
import requests


class HTTPSClient(BaseClient):
    allowed_authorizer_types = (AccessTokenAuthorizer, RefreshTokenAuthorizer)

    error_class = HTTPSClientException

    def __init__(self, authorizer=None, base_url='', **kwargs):
        super().__init__(
            self, "http_client", base_url=base_url,
            authorizer=authorizer, **kwargs
        )

    def put(self, path, params=None, headers=None, allow_redirects=False,
            filename=None, response_class=None, retry_401=True):
        if not filename:
            raise ValueError('No filename provided')
        with open(filename, 'rb') as data:
            self.logger.debug('PUT to {} with params {}'.format(path, params))
            return self.send_custom_request(
                "PUT", path, params=params,
                headers=headers, allow_redirects=allow_redirects, data=data,
                response_class=response_class, retry_401=retry_401
            )

    def send_custom_request(self, method, path, params=None, headers=None,
                            allow_redirects=False, data=None,
                            response_class=None, retry_401=True):
        rheaders = dict(self._headers)
        # expand
        if headers is not None:
            rheaders.update(headers)

        # add Authorization header, or (if it's a NullAuthorizer) possibly
        # explicitly remove the Authorization header
        if self.authorizer is not None:
            self.logger.debug(
                "request will have authorization of type {}".format(
                    type(self.authorizer)
                )
            )
            self.authorizer.set_authorization_header(rheaders)

        url = slash_join(self.base_url, path)
        self.logger.debug("request will hit URL:{}".format(url))

        # because a 401 can trigger retry, we need to wrap the retry-able thing
        # in a method
        def send_request():
            try:
                return self._session.request(
                    method=method,
                    url=url,
                    headers=rheaders,
                    data=data,
                    params=params,
                    allow_redirects=allow_redirects,
                    verify=self._verify,
                    timeout=self._http_timeout,
                )
            except requests.RequestException as e:
                self.logger.error("NetworkError on request")
                raise exc.convert_request_exception(e)

        # initial request
        r = send_request()

        self.logger.debug("Request made to URL: {}".format(r.url))

        # potential 401 retry handling
        if r.status_code == 401 and retry_401 and self.authorizer is not None:
            self.logger.debug("request got 401, checking retry-capability")
            # note that although handle_missing_authorization returns a T/F
            # value, it may actually mutate the state of the authorizer and
            # therefore change the value set by the `set_authorization_header`
            # method
            if self.authorizer.handle_missing_authorization():
                self.logger.debug("request can be retried")
                self.authorizer.set_authorization_header(rheaders)
                r = send_request()

        if 200 <= r.status_code < 400:
            self.logger.debug(
                "request completed with response code: {}".format(
                    r.status_code)
            )
            if response_class is None:
                return self.default_response_class(r, client=self)
            else:
                return response_class(r, client=self)

        self.logger.debug(
            "request completed with (error) response code: {}".format(
                r.status_code)
        )
        raise self.error_class(r)

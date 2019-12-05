import re
import logging
from globus_sdk import AccessTokenAuthorizer, RefreshTokenAuthorizer
from globus_sdk.base import BaseClient, slash_join
from globus_sdk.response import GlobusResponse
from pilot.exc import HTTPSClientException
from globus_sdk import exc
import requests
from requests_toolbelt import multipart

log = logging.getLogger(__name__)

# Pattern of how ranges must be given on the command line
RANGE = re.compile(r'^(\d+-\d+)(,\d+-\d+)*$')


class FileContentResponse(GlobusResponse):

    def __init__(self, response, client):
        super().__init__(response, client)

    @property
    def text(self):
        return str(self.data)

    @property
    def data(self):
        byte_content = b''
        for content in self.iter_content:
            byte_content += content
        return byte_content.decode('utf-8')

    @property
    def iter_content(self):
        content_type = self._data.headers.get('Content-Type', '')
        if 'multipart/byteranges' in content_type:
            md = multipart.decoder.MultipartDecoder.from_response(self._data)
            return [part.content for part in md.parts]
        return self._data.iter_content(chunk_size=(2**20 * 2))

    @property
    def raw_response(self):
        return self._data


class HTTPFileClient(BaseClient):
    allowed_authorizer_types = (AccessTokenAuthorizer, RefreshTokenAuthorizer)

    error_class = HTTPSClientException
    default_response_class = GlobusResponse
    file_content_response_class = FileContentResponse

    def __init__(self, authorizer=None, base_url='', **kwargs):
        super().__init__(
            self, "http_client", base_url=base_url,
            authorizer=authorizer, **kwargs
        )

    def get(self, path, params=None, headers=None, allow_redirects=False,
            filename=None, response_class=None, retry_401=True, range=None):
        headers = headers or {}
        if range:
            if not isinstance(range, str) or not re.match(RANGE, range):
                raise ValueError('Ranges must be a string of the pattern: '
                                 '"1-2,3-4" where each number is a byte range')
            headers['Range'] = 'bytes={}'.format(range)
        response_class = response_class or self.file_content_response_class
        return self.send_custom_request(
            'GET', path, params=params,
            headers=headers, allow_redirects=allow_redirects,
            response_class=response_class, retry_401=retry_401, stream=True
        )

    def put(self, path, params=None, headers=None, allow_redirects=False,
            filename=None, response_class=None, retry_401=True, data=None):
        if data:
            return self.send_custom_request(
                "PUT", path, params=params,
                headers=headers, allow_redirects=allow_redirects,
                response_class=response_class, retry_401=retry_401, data=data
            )
        if not filename:
            raise ValueError('No filename provided')
        with open(filename, 'rb') as data:
            self.logger.debug('PUT to {} with params {}'.format(path, params))
            return self.send_custom_request(
                "PUT", path, params=params,
                headers=headers, allow_redirects=allow_redirects, data=data,
                response_class=response_class, retry_401=retry_401,
            )

    def delete(self, path, **kwargs):
        return self.send_custom_request('DELETE', path, **kwargs)

    def send_custom_request(self, method, path, headers=None,
                            allow_redirects=False, response_class=None,
                            retry_401=True, **kwargs):
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

        if path.startswith('https://') or path.startswith('http://'):
            url = path
        else:
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
                    allow_redirects=allow_redirects,
                    verify=self._verify,
                    timeout=self._http_timeout,
                    **kwargs
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

        return self.handle_response(r, response_class)

    def handle_response(self, response, response_class=None):
        if 200 <= response.status_code < 400:
            self.logger.debug(
                "request completed with response code: {}".format(
                    response.status_code)
            )
            if response_class is None:
                return self.default_response_class(response, client=self)
            else:
                return response_class(response, client=self)

        self.logger.debug(
            "request completed with (error) response code: {}".format(
                response.status_code)
        )
        raise self.error_class(response)


class NexusClient(BaseClient):
    """This is a custom nexus client for fetching groups. It is not available
    outside of this client."""
    allowed_authorizer_types = (AccessTokenAuthorizer, RefreshTokenAuthorizer)
    error_class = HTTPSClientException
    default_response_class = GlobusResponse
    file_content_response_class = FileContentResponse

    def __init__(self, authorizer=None, base_url='', **kwargs):
        base_url = base_url or 'https://nexus.api.globusonline.org/groups/'
        super().__init__(
            self, "custom_pilot_nexus_client", base_url=base_url,
            authorizer=authorizer, **kwargs
        )

    def get_subgroups(self, group, **params):
        """
        Get a list of Globus Sub-Groups for a given group. Max depth is by
        default 100.
        """
        log.debug('Nexus GET for subgroups in "{}"'.format(group))
        request_params = {'root': group, 'depth': 100}
        request_params.update(params)
        return self.get('list', params=request_params)

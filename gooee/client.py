# -*- coding: utf-8 -*-
# Copyright 2019 Gooee.com, LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at:
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# or in the "LICENSE" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from __future__ import unicode_literals

from platform import platform

import requests
from six import string_types

from .compat import json
from .decorators import resource
from .exceptions import IllegalHttpMethod, GooeeException
from . import __version__
from .utils import (
    format_path,
    GOOEE_API_URL
)


class GooeeClient(object):
    """Gooee HTTP client class."""

    allowed_methods = ('get', 'post', 'put', 'patch', 'delete', 'options')

    def __init__(self, api_base_url=GOOEE_API_URL):
        self.api_base_url = api_base_url
        self.auth_token = ''
        self.api_token = ''

    def _request(self, method, path, headers=None, data=None, params=None):
        """Request helper."""
        if method not in self.allowed_methods:
            msg = 'HTTP method {} not supported. Needs to be one of: {}'.format(
                method, self.allowed_methods)
            raise IllegalHttpMethod(msg)

        url = format_path(path, self.api_base_url)

        headers_final = self.default_headers
        headers_final.update(headers or {})
        if not headers_final['Authorization']:
            headers_final.pop('Authorization')

        if data and not isinstance(data, string_types):
            data = json.dumps(data)

        response = getattr(requests, method)(
            url, headers=headers_final, data=data, params=params)

        return response

    def authenticate(self, username=None, password=None, api_token=None):
        """Assert and store API authentication credentials for future requests."""
        # Authenticate with a username and password for a JWT token.
        if username and password:
            payload = {
                'username': username,
                'password': password,
            }
            response = self.post('/auth/login', data=payload)

            # If the status was all good, stash the JWT token.
            if response.status_code != 200:
                raise GooeeException('Could not authenticate with the API username and password')

            self.auth_token = 'JWT {token}'.format(token=response.json['token'])

        # Authenticate with an API token.
        elif api_token:
            response = self.get('/me', headers={'Authorization': api_token})
            if response.status_code != 200:
                raise GooeeException('Could not authenticate with the API token')

            self.api_token = api_token

        else:
            raise GooeeException('Insufficient authentication credentials provided')

        return response

    @property
    def default_headers(self):
        """Default headers to talk to the API with."""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': self.api_token or self.auth_token,
            'User-Agent': 'gooee-python-sdk {version} ({system})'.format(
                version=__version__,
                system=platform(),
            )
        }
        return headers

    @resource
    def get(self, path, params=None):
        return self._request('get', path, params=params)

    @resource
    def post(self, path, headers=None, data=None, params=None):
        return self._request('post', path, headers=headers, data=data, params=params)

    @resource
    def put(self, path, data=None, params=None):
        return self._request('put', path, data=data, params=params)

    @resource
    def patch(self, path, data=None, params=None):
        return self._request('patch', path, data=data, params=params)

    @resource
    def delete(self, path, params=None):
        return self._request('delete', path, params=params)

    @resource
    def options(self, path, params=None):
        return self._request('options', path, params=params)

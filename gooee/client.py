# -*- coding: utf-8 -*-
# Copyright 2017 Gooee.com, LLC. All Rights Reserved.
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

from .compat import json
from .decorators import resource
from .exceptions import (
    IllegalHttpMethod,
)
from . import __version__
from .utils import (
    format_path,
    GOOEE_API_URL
)


class Gooee(object):
    """Gooee HTTP client class."""

    allowed_methods = ['post', 'get', 'delete']

    def __init__(self, api_base_url=GOOEE_API_URL):
        self.api_base_url = api_base_url
        self.auth_token = ''

    def authenticate(self, username, password):
        payload = {"username": username,
                   "password": password}
        token = self.post('/auth/login', payload).get('token')
        self.auth_token = 'JWT {token}'.format(token=token)

    @property
    def headers(self):
        headers = {
            "content-type": "application/json",
            "Authorization": self.auth_token,
            "User-Agent": "gooee-python-sdk {version} ({system})".format(
                version=__version__,
                system=platform(),
            )
        }
        return headers

    def api(self, method, path, data):
        method = method.strip().lower()
        if method not in self.allowed_methods:
            msg = "The '{0}' method is not accepted by Gooee SDK.".format(method)
            raise IllegalHttpMethod(msg)
        method = getattr(self, method)
        return method(path, data)

    @resource
    def get(self, path, data=None):
        path = format_path(path, self.api_base_url)

        if data is None:
            data = {}

        return requests.get(path, headers=self.headers, params=data or {})

    @resource
    def post(self, path, data=None):
        path = format_path(path, self.api_base_url)
        json_data = json.dumps(data or {})
        return requests.post(path, headers=self.headers, data=json_data)

    @resource
    def put(self, path, data=None):
        path = format_path(path, self.api_base_url)
        json_data = json.dumps(data or {})
        return requests.put(path, headers=self.headers, data=json_data)

    @resource
    def delete(self, path, data=None):
        path = format_path(path, self.api_base_url)
        return requests.delete(path, headers=self.headers, data=data or {})

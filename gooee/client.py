# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from platform import platform

import requests

from .compat import json
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

    def __init__(self, oauth_token, api_base_url=GOOEE_API_URL):
        self.oauth_token = oauth_token
        self.api_base_url = api_base_url

    @property
    def headers(self):
        headers = {
            "content-type": "application/json",
            "Authorization": "",
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

    def get(self, path, data=None):
        # Get the function path
        path = format_path(path, self.api_base_url)

        if data is None:
            data = {}

        return requests.get(path, headers=self.headers, params=data or {})

    def post(self, path, data=None):
        path = format_path(path, self.api_base_url)
        json_data = json.dumps(data or {})
        return requests.post(path, headers=self.headers, data=json_data)

    def delete(self, path, data=None):
        path = format_path(path, self.api_base_url)
        return requests.delete(path, headers=self.headers, data=data or {})

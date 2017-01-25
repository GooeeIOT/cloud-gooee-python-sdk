# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from platform import platform

import requests

from .compat import json, string_type
from .exceptions import (
    IllegalHttpMethod,
)
from . import __version__


class Gooee(object):

    allowed_methods = ['post', 'get', 'delete']

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

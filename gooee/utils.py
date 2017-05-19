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
from os import environ

from six import string_types
from six.moves import urllib_parse

from .exceptions import InvalidResourcePath

GOOEE_API_URL = environ.get('GOOEE_API_URL', 'https://dev-api.gooee.io/')
GOOEE_API_PATH = urllib_parse.urlparse(GOOEE_API_URL).path


def format_path(path, api_base_url=GOOEE_API_URL):
    error_msg = 'The path argument must be a string that begins with "/"'
    if not isinstance(path, string_types):
        raise InvalidResourcePath(error_msg)

    # Using the HTTP shortcut
    if path.startswith('/'):
        return urllib_parse.urljoin(api_base_url, path.lstrip('/'))

    return path

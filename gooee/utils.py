# -*- coding: utf-8 -*-
from os import environ

from .compat import (
    string_type,
    urlparse,
    urljoin
)
from .exceptions import (
    InvalidResourcePath,
)

GOOEE_API_URL = environ.get('GOOEE_API_URL', 'https://dev-api.gooee.io/')
GOOEE_API_PATH = urlparse(GOOEE_API_URL).path


def format_path(path, api_base_url=GOOEE_API_URL):
    error_msg = "The path argument must be a string that begins with '/'"
    if not isinstance(path, string_type):
        raise InvalidResourcePath(error_msg)

    # Using the HTTP shortcut
    if path.startswith("/"):
        return urljoin(api_base_url, path.lstrip('/'))
    raise InvalidResourcePath(error_msg)


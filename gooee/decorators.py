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
import functools

import requests

from .exceptions import InternetConnectionError
from .models import Resource


def resource(func):
    """Converts the response to a Resource."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            response = func(*args, **kwargs)
        except requests.exceptions.ConnectionError as e:
            raise InternetConnectionError(e)

        return Resource(response)

    return wrapper

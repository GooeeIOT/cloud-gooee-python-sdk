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

import logging

__author__ = 'Gooee LLC'
__email__ = 'dairon@gooee.com'
__version__ = '0.0.1'

from .client import GooeeClient  # noqa


def set_stream_logging(level=logging.DEBUG, format_string=None):
    """
    Add a stdout log handler with provided level to the SDK operations.
        >>> import logging
        >>> import gooee
        >>> gooee.set_stream_logging(logging.INFO)
    :type level: int
    :param level: Logging level, e.g. ``logging.INFO``
    :type format_string: str
    :param format_string: Log message format
    """
    if format_string is None:
        format_string = '%(asctime)s %(name)s [%(levelname)s] %(message)s'

    logger = logging.getLogger('gooee')
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class NullHandler(logging.Handler):
    """
    Set up logging to ``/dev/null`` like a library is supposed to.
    http://docs.python.org/3.3/howto/logging.html#configuring-logging-for-a-library
    """

    def emit(self, record):
        pass


logging.getLogger('gooee').addHandler(NullHandler())

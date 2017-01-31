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
import sys

PY3 = sys.version_info[0] == 3
OLD_PY2 = sys.version_info[:2] < (2, 7)


if PY3:
    string_type = str
else:
    string_type = basestring


try:  # pragma: no cover
    # For python 2.6
    import simplejson as json
except ImportError:
    # For python 2.7+
    import json  # noqa

try:
    from urllib.parse import (
        urlparse,
        urljoin,
    )
except ImportError:
    from urlparse import (  # noqa
        urlparse,
        urljoin,
    )

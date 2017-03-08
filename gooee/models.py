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
import pprint


class Resource(dict):

    is_list = None
    is_paginated = None
    # pagination dict w/ keys: object_count, page_number, page_size, page_count
    pagination = None
    type = ""
    id = None
    pk = None

    @classmethod
    def create(cls, response):
        data = response.json() or {}
        gooeeobj = cls(data)
        try:
            # Strip out URL parameters for resource_uri
            gooeeobj.resource_uri = response.url[:response.url.index('?')]
        except ValueError:
            gooeeobj.resource_uri = response.url
        gooeeobj.ok = response.ok
        gooeeobj.elapsed = response.elapsed
        gooeeobj.headers = response.headers
        gooeeobj.reason = response.reason
        gooeeobj.status_code = response.status_code
        gooeeobj.request = response.request
        # if it's paginated, it's a list, otherwise we don't know yet
        # TODO: Implement pagination from headers.
        gooeeobj.pagination = data.get('pagination', False)
        gooeeobj.is_list = bool(gooeeobj.pagination)  # gooeeobj.is_paginated = True
        gooeeobj.is_paginated = bool(gooeeobj.pagination)
        gooeeobj.pk = gooeeobj.id = data.get('id')
        gooeeobj.pagination = data.get('pagination')
        return gooeeobj

    @property
    def pretty(self):
        return pprint.pformat(self)

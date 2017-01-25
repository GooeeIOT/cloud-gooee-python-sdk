# -*- coding: utf-8 -*-
import pprint


class GooeeObject(dict):

    is_list = None
    is_paginated = None
    # pagination dict w/ keys: object_count, page_number, page_size, page_count
    pagination = None
    type = ""
    id = None
    pk = None

    @classmethod
    def create(cls, response):
        data = response.json()
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

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
from .compat import json


class Resource(object):
    """Objectify a Response."""

    def __init__(self, response):

        try:
            self.json = response.json()
        except json.decoder.JSONDecodeError:
            # This happens on a DELETE or a response that returns
            # nothing. We could improve this to only raise when it isn't
            # that case... but we'd need to know it was expected... or
            # not. This would also occur when DJANGO is in DEBUG mode
            # and the traceback webpage is returned in the response.
            self.json = None

        self.text = response.text
        self.elapsed = response.elapsed
        self.headers = response.headers
        self.reason = response.reason
        self.status_code = response.status_code
        self.request = response.request
        self._response = response

        self._populate_prev_and_next_links()

    def _populate_prev_and_next_links(self):
        """Populate the previous and next Link headers on the request."""
        self._prev_link = self._next_link = None
        links = self._response.headers.get('Link', None)
        if links:
            for link, rel in (link.split('; ') for link in links.split(', ')):
                link = link[1:-1]
                rel = rel.split('"')[1]
                if rel == 'prev':
                    self._prev_link = link
                elif rel == 'next':
                    self._next_link = link

    def __repr__(self):
        return '<{} {} {}:{}>'.format(
            self.request.method,
            self.request.url,
            self.status_code,
            self.reason
        )

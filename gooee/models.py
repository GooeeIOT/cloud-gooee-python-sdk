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
import json


class Resource(object):
    """
    Objectify a Response.
    """

    def __init__(self, response):
        try:
            self.json = response.json()
        except json.decoder.JSONDecodeError:
            self.json = None
        self.text = response.text
        self.elapsed = response.elapsed
        self.headers = response.headers
        self.reason = response.reason
        self.status_code = response.status_code
        self.request = response.request

    def __repr__(self):
        return '<{} {} {}:{}>'.format(self.request.method, self.request.url,
                                      self.status_code, self.reason)

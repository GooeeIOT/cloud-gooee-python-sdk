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
import logging
from jinja2 import FileSystemLoader, Environment

logger = logging.getLogger(__name__)


class ResourceFactory(object):

    def __init__(self):
        pass

    def load_from_definition(self, resource_name):
        pass

    def _load_attributes(self):
        pass

    def _load_actions(self):
        pass

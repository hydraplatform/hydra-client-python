#!/usr/bin/env python
# -*- coding: utf-8 -*-

# (c) Copyright 2013 to 2017 University of Manchester
#
# HydraPlatform is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# HydraPlatform is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with HydraPlatform.  If not, see <http://www.gnu.org/licenses/>
#

import json

import logging
log = logging.getLogger(__name__)

from datetime import datetime

class ExtendedDict(dict):
    """
        A dictionary object whose attributes can be accesed via a '.'.
        Pass in a nested dictionary
    """
    def __init__(self, obj_dict, parent=None):

        for k, v in obj_dict.items():
            if isinstance(v, ExtendedDict):
                setattr(self, k, v)
            elif isinstance(v, dict):
                setattr(self, k, ExtendedDict(v, obj_dict))
            elif isinstance(v, list):
                l = [ExtendedDict(item, obj_dict) for item in v]
                setattr(self, k, l)
            else:
                setattr(self, k, v)

    def __getattr__(self, name):
        if name.startswith('__') and name.endswith('__'):
            return super(ExtendedDict, self).__getattr__(name)
        else:
            return self.get(name, None)

    def __setattr__(self, key, value):
        self[key] = value

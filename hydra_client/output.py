# (c) Copyright 2013, 2014, University of Manchester
#
# HydraLib is free software: you can redistribute it and/or modify
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
# -*- coding: utf-8 -*-

__all__ = ['write_progress', 'write_output']

import os
import logging
log = logging.getLogger(__name__)

from hydra_base import config

import sys


def write_progress(x, y):
    """
        Format and print a progress message to stdout so that
        a UI or other can pick it up and use it.
    """
    msg = "!!Progress %s/%s" % (x, y)
    print(msg)
    sys.stdout.flush()


def write_output(text):
    """
        Format and print a freeform message to stdout so that
        the UI or other can pick it up and use it
    """
    msg = "!!Output %s" % (text,)
    print(msg)
    sys.stdout.flush()

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

__all__ = ['RequestError']

class RequestError(Exception):
    pass

class HydraClientError(Exception):
    """
    Base class for all Hydra errors.
    """
    def __init__(self, message=None, *args, **kwargs):
        super(HydraClientError, self).__init__(message, *args, **kwargs)
        self.message = message

    def __str__(self):
        return self.message if self.message else "An error occurred in Hydra."
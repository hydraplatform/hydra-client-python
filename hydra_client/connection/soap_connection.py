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

#JSONConnection and JsonCOnnection are synonyums, and used for backward compatibility
__all__ = ['SoapConnection', 'SOAPConnection']
import requests
import json

import logging
log = logging.getLogger(__name__)

from suds.client import Client
from suds.plugin import MessagePlugin

from base_connection import BaseConnection

import getpass

from ..exception import RequestError
import time
import os
import warnings

class FixNamespace(MessagePlugin):
    """Hopefully a temporary fix for an unresolved namespace issue.
    """
    def marshalled(self, context):
        self.fix_ns(context.envelope)

    def fix_ns(self, element):
        if element.prefix == 'xs':
            element.prefix = 'ns0'

        for e in element.getChildren():
            self.fix_ns(e)

class SOAPConnection(BaseConnection):

    def __init__(self, url=None, session_id=None, app_name=None):
        super(SOAPConnection, self).__init__(app_name=app_name)

        self.url = self.get_url(url, 'soap?wsdl')

        log.info("Setting URL %s", self.url)

        self.app_name = app_name
        self.session_id = session_id
        self.retxml = False
        self.client = Client(self.url,
                             timeout=3600,
                             plugins=[FixNamespace()],
                             retxml=self.retxml)
        self.client.add_prefix('hyd', 'server.complexmodels')

        cache = self.client.options.cache
        cache.setduration(days=10)

    def login(self, username=None, password=None):
        """Establish a connection to the specified server. If the URL of the
        server is not specified as an argument of this function, the URL
        defined in the configuration file is used."""

        # Connect
        token = self.client.factory.create('RequestHeader')
        if self.session_id is None:
            parsed_username, parsed_password = self.get_username_and_password(username, password)

            login_response = self.client.service.login(parsed_username, parsed_password)
            token.user_id = login_response.user_id
            self.user_id = login_response.user_id

        #This needs to be 'sessionid' instead if 'session_id' because of apache
        #not handling '_' well in request headers
        self.client.set_options(soapheaders=token)

        return token.user_id

class SoapConnection(SOAPConnection):
    def __init__(self, *args, **kwargs):
        super(SoapConnection, self).__init__()
        warnings.warn(
            'This class will will be deprecated in favour of `SOAPConnection`'
            ' in a future release. Please update your code to use `SOAPConnection`'
            ' instead.',
             PendingDeprecationWarning
        )

def object_hook(x):
    return ExtendedDict(x)

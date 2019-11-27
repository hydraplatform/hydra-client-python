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

#RemoteJSONConnection and JsonConnection are synonyums, and used for backward compatibility
__all__ = ['RemoteJSONConnection', 'JsonConnection']
import requests
import json

import logging
log = logging.getLogger(__name__)

from ..objects import ExtendedDict

from hydra_client.exception import RequestError
import time
import warnings

from .base_connection import BaseConnection


class RemoteJSONConnection(BaseConnection):
    """ Remote connection to a Hydra server. """
    def __init__(self, url=None, session_id=None, app_name=None):
        super(RemoteJSONConnection, self).__init__(app_name=app_name)

        self.user_id  = None


        self.url = self.get_url(url, 'json')
        self.app_name = app_name if app_name else ''
        self.session_id = session_id

    def call(self, func, *args, **kwargs):
        """
            Call an arbitrary hydra server function, identified by the 'name' parameter

            example:
                self.call('get_network', {'network_id':2})

        """
        start_time = time.time()
        log.info("Calling: %s" % (func))

        if len(args) == 0:
            fn_args = kwargs
        else:
            fn_args = args[0]

        # TODO add kwargs?
        call = {func: fn_args}
        headers = {
                   'Content-Type': 'application/json',
                   'appname': self.app_name,
                   }
        log.info("Args %s", call)
        cookie = {'beaker.session.id':self.session_id,
                  'user_id': str(self.user_id),
                  'appname': self.app_name.replace(' ', '_')#for some reason, beaker fails when the appname cookie has a space in it
                 }

        r = requests.post(self.url, data=json.dumps(call), headers=headers, cookies=cookie)

        if not r.ok:
            try:
                resp = json.loads(r.content)
                err = "%s:%s" % (resp['faultcode'], resp['faultstring'])
            except:
                log.debug("Headers: %s"%headers)
                log.debug("Url: %s"%self.url)
                log.debug("Content: %s"%json.dumps(call))

                if r.content != '':
                    err = r.content
                else:
                    err = "An unknown server has occurred."

                if self.url.find('soap') > 0:
                    log.info('The URL %s contains "soap". Is the wrong URL being used?', self.url)
                    err.append(' -- A shot in the dark: the URL contains the word "soap".'+
                                ', but this is a JSON-based plugin.' +
                                ' Perhaps the wrong URL is being specified?')

            raise RequestError(err)

        if self.session_id is None:

            self.session_id = r.cookies['beaker.session.id']
            log.info(self.session_id)

        ret_obj = json.loads(r.content, object_hook=object_hook)

        log.info('done (%s)'%(time.time() -start_time,))

        return ret_obj

    def login(self, username=None, password=None):

        new_username, new_password = self.get_username_and_password(username, password)

        login_params = {'username': new_username, 'password': new_password}

        resp = self.call('login', login_params)
        self.user_id = int(resp.user_id)
        #set variables for use in request headers
        log.info("Login response OK for user: %s", self.user_id)


class JsonConnection(RemoteJSONConnection):
    def __init__(self, *args, **kwargs):
        super(JsonConnection, self).__init__()
        warnings.warn(
            'This class will will be deprecated in favour of `RemoteJSONConnection`'
            ' in a future release. Please update your code to use `RemoteJSONConnection`'
            ' instead.',
             PendingDeprecationWarning
        )

def object_hook(x):
    return ExtendedDict(x)

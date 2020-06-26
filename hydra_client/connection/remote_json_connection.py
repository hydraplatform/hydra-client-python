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
import json
import time
import warnings
import logging
import requests

from hydra_base.lib.objects import JSONObject

from hydra_client.exception import RequestError

from .base_connection import BaseConnection

log = logging.getLogger(__name__)


class RemoteJSONConnection(BaseConnection):
    """ Remote connection to a Hydra server. """
    def __init__(self, url=None, session_id=None, app_name=None, test_server=None):
        """
            args:
                url: The url of the hydra platform server
                session_id: The session ID if one exists for that user already
                app_name: The name of the app making the requests
                test_server: A Spyne NullServer object, which if not null is used
                              for testing purposes

        """
        super(RemoteJSONConnection, self).__init__(app_name=app_name)

        self.user_id  = None
        self.url = self.get_url(url, 'json')
        self.app_name = app_name if app_name else ''
        self.session_id = session_id
        self.test_server = None

        if test_server is not None:
            self.test_server = test_server
            self.session_id = 'null_session'

    def _test_call(self, func_name, *args, **kwargs):
        """
            Call the function in a spyne null server instead of a remote web server
            for unit testing purposes
        """
        func = getattr(self.test_server.service, func_name)

        # Add user_id to the kwargs if not given and logged in.
        if 'user_id' not in kwargs and self.user_id is not None:
            kwargs['user_id'] = self.user_id

        class FakeHeader():
            def __init__(self, user_id):
                self.user_id = user_id

        func._in_header = FakeHeader(self.user_id)

        for k, v in kwargs.items():
            if v is True:
                kwargs[k] = 'Y'
            elif v is False:
                kwargs[k] = 'N'

        # Call the NullServer function
        ret = func(*args, **kwargs)
        x = list(ret)
        raw_ret = x[0]

        json_ret = json.loads(raw_ret)

        #Return value is a generator so we need to convert it to a list and return
        #the first element
        try:
            if isinstance(json_ret, list):
                try:
                    return [JSONObject(r) for r in json_ret]
                except:
                    return json_ret
            else:
                return JSONObject(json_ret)
        except ValueError:
            return json_ret

    def call(self, func, *args, **kwargs):
        """
            Call an arbitrary hydra server function, identified by the 'name' parameter

            example:
                self.call('get_network', {'network_id':2})

        """

        if self.test_server is not None:
            return self._test_call(func, *args, **kwargs)

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

        resp = self.call('login', **login_params)

        self.user_id = int(resp.user_id)
        #set variables for use in request headers
        log.info("Login response OK for user: %s", self.user_id)

        return self.user_id, self.session_id


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
    return JSONObject(x)

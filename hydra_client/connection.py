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
__all__ = ['JSONConnection', 'JsonConnection', 'SoapConnection', 'SOAPConnection']
import requests
import json

import logging
log = logging.getLogger(__name__)

from suds.client import Client
from suds.plugin import MessagePlugin

import hydra_base as hb
from hydra_base import config
from hydra_base.lib.objects import JSONObject

from .exception import RequestError
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


def _get_path(url):
    """
        Find the path in a url. (The bit after the hostname
        and port).
        ex: http://www.google.com/test
        returns: test
    """

    if url.find('http://') == 0:
        url = url.replace('http://', '')
    if url.find('https://') == 0:
        url = url.replace('https://', '')

    hostname = url.split('/')
    if len(hostname) == 1:
        return ''
    else:
        return "/%s" % ("/".join(hostname[1:]))


def _get_hostname(url):
    """
        Find the hostname in a url.
        Assume url can take these forms. The () means optional.:
        1: (http(s)://)hostname
        2: (http(s)://)hostname:port
        3: (http(s)://)hostname:port/path
    """

    if url.find('http://') == 0:
        url = url.replace('http://', '')
    if url.find('https://') == 0:
        url = url.replace('https://', '')

    hostname = url.split('/')[0]

    #is a user-defined port specified?
    port_parts = url.split(':')
    if len(port_parts) > 1:
        hostname = port_parts[0]

    return hostname


def _get_port(url):
    """
        Get the port of a url.
        Default port is 80. A specified port
        will come after the first ':' and before the next '/'
    """

    if url.find('http://') == 0:
        url = url.replace('http://', '')
        port = 80
    if url.find('https://') == 0:
        url = url.replace('https://', '')
        port = 443

    url_parts = url.split(':')

    if len(url_parts) == 1:
        return port
    else:
        port_part = url_parts[1]
        port_section = port_part.split('/')[0]
        try:
            int(port_section)
        except:
            return port
        return int(port_section)

    return port


def _get_protocol(url):
    """
        Get the port of a url.
        Default port is 80. A specified port
        will come after the first ':' and before the next '/'
    """

    if url.find('http://') == 0:
        return 'http'
    elif url.find('https://') == 0:
        return 'https'
    else:
        return 'http'


# Do this for backward compatibility
class BaseConnection(object):
    """ Common base class for all connection subclasses. """
    def __init__(self, *args, **kwargs):
        super(BaseConnection, self).__init__()
        self.app_name = kwargs.get('app_name', None)

    def call(self, func_name, *args, **kwargs):
        """ Call a hydra-base function by name. """
        raise NotImplementedError()

    def login(self):
        raise NotImplementedError()

    def __getattr__(self, name):
        """
            Here we redirect the function call to the local library function or
            into the 'call' function, which uses a http request
        """
        def wrapped(*args, **kwargs):
            return self.call(name, *args, **kwargs)
        return wrapped


class RemoteJSONConnection(BaseConnection):
    """ Remote connection to a Hydra server. """
    def __init__(self, url, session_id=None, app_name=None):
        super(RemoteJSONConnection, self).__init__(app_name=app_name)

        self.user_id  = None

        if url is None:
            port = config.getint('hydra_client', 'port', 80)
            domain = config.get('hydra_client', 'domain', '127.0.0.1')
            path = config.get('hydra_client', 'json_path', 'json')
            # The domain may or may not specify the protocol, so do a check.
            if domain.find('http') == -1:
                self.url = "http://%s:%s/%s" % (domain, port, path)
            else:
                self.url = "%s:%s/%s" % (domain, port, path)
        else:
            log.info("Using user-defined URL: %s", url)
            port = _get_port(url)
            hostname = _get_hostname(url)
            path = _get_path(url)
            protocol = _get_protocol(url)
            self.url = "%s://%s:%s%s/json" % (protocol, hostname, port, path)

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
            fn_args = {}
        else:
            fn_args = args[0]
        # TODO add kwargs?
        call = {func: fn_args}
        headers = {
                   'Content-Type': 'application/json',
                   'appname': self.app_name,
                   }
        log.info("Args %s", call)
        cookie = {'beaker.session.id':self.session_id, 'appname:': self.app_name}
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

        if username is None:
            username = config.get('hydra_client', 'user')
        if password is None:
            password = config.get('hydra_client', 'password')
        login_params = {'username': username, 'password': password}

        resp = self.call('login', login_params)
        self.user_id = int(resp.user_id)
        #set variables for use in request headers
        log.info("Login response OK for user: %s", self.user_id)


import collections
import six
def args_to_json_object(*args):
    for arg in args:
        if isinstance(arg, six.string_types):
            yield arg
        elif isinstance(arg, (int, float)):
            yield arg
        elif isinstance(arg, collections.Mapping):
            yield JSONObject(arg)
        elif isinstance(arg, collections.Iterable):
            yield [JSONObject(v) for v in arg]
        else:
            yield JSONObject(arg)


class JSONConnection(BaseConnection):
    """ Local connection to a Hydra database using hydra_base directly."""
    def __init__(self, *args, **kwargs):
        super(JSONConnection, self).__init__(*args, **kwargs)
        self.user_id = None
        db_url = kwargs.get('db_url', None)
        self.autocommit = kwargs.get('autocommit', True)
        hb.db.connect(db_url)

    def call(self, func_name, *args, **kwargs):
        func = getattr(hb, func_name)

        # Add user_id to the kwargs if not given and logged in.
        if 'user_id' not in kwargs and self.user_id is not None:
            kwargs['user_id'] = self.user_id

        # Convert the arguments to JSON objects
        json_obj_args = list(args_to_json_object(*args))

        # Call the HB function
        ret = func(*json_obj_args, **kwargs)
        for o in args_to_json_object(ret):
            if self.autocommit is True:
                hb.db.commit_transaction()
            return o

    def login(self, username=None, password=None):

        # TODO add support for token based authentication when merged upstream.
        if username is None:
            # Try to get user name from environment
            try:
                username = os.environ['HYDRA_USERNAME']
            except KeyError:
                raise ValueError('No username found.')
            else:
                log.debug('Using username from environment.')

        if password is None:
            try:
                username = os.environ['HYDRA_PASSWORD']
            except KeyError:
                raise ValueError('No password found for user "{}"'.format(username))
            else:
                log.debug('Using password from environment.')

        self.user_id = hb.hdb.login_user(username, password)

class JsonConnection(RemoteJSONConnection):
    def __init__(self, *args, **kwargs):
        super(JsonConnection, self).__init__()
        warnings.warn(
            'This class will will be deprecated in favour of `RemoteJSONConnection`'
            ' in a future release. Please update your code to use `RemoteJSONConnection`'
            ' instead.',
             PendingDeprecationWarning
        )


class SOAPConnection(object):

    def __init__(self, url=None, session_id=None, app_name=None):
        if url is None:
            port = config.getint('hydra_client', 'port', 80)
            domain = config.get('hydra_client', 'domain', '127.0.0.1')
            path = config.get('hydra_client', 'soap_path', 'soap')
            #The domain may or may not specify the protocol, so do a check.
            if domain.find('http') == -1:
                self.url = "http://%s:%s/%s?wsdl" % (domain, port, path)
            else:
                self.url = "%s:%s/%s?wsdl" % (domain, port, path)
        else:
            log.info("Using user-defined URL: %s", url)
            port = _get_port(url)
            hostname = _get_hostname(url)
            path = _get_path(url)
            protocol = _get_protocol(url)
            self.url = "%s://%s:%s%s/soap?wsdl" % (protocol, hostname, port, path)
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
            if username is None:
                user = config.get('hydra_client', 'user')
            if password is None:
                passwd = config.get('hydra_client', 'password')
            login_response = self.client.service.login(user, passwd)
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
    return JSONObject(x)

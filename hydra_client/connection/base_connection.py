from .. import config

import collections
import six

import os

import getpass

import logging
log = logging.getLogger(__name__)

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

    def get_url(self, url, path):
        if url is None:
            port = config.port
            domain = config.domain
            # The domain may or may not specify the protocol, so do a check.
            if domain.find('http') == -1:
                ret_url = "http://%s:%s/%s" % (domain, port, path)
            else:
                ret_url = "%s:%s/%s" % (domain, port, path)
        else:
            log.info("Using user-defined URL: %s", url)
            port = self.get_port(url)
            hostname = self.get_hostname(url)
            path = self.get_path(url)
            protocol = self.get_protocol(url)
            ret_url = "%s://%s:%s/%s" % (protocol, hostname, port, path)

        return ret_url

    def get_path(self, url):
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


    def get_hostname(self, url):
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


    def get_port(self, url):
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


    def get_protocol(self, url):
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

    def get_username_and_password(self, username, password):
        """
            Taking a username and password as arguments, return a username and password
            The incoming username and password can be null, in which case check the
            'HYDRA_USERNAME' and 'HYDRA_PASSWORD' environment variables respectively.
            Failing that, prompt the user for their credentials.
        """
        # TODO add support for token based authentication when merged upstream.
        if username is None:
            log.info("No username specified. Defaulting looking at 'HYDRA_USERNAME'")
            ret_username = os.environ.get('HYDRA_USERNAME')

            if username is None:
                log.info("HYDRA_USERNAME usernams is None, prompting user")
                ret_username = raw_input('Username:')
        else:
            ret_username = username

        if password is None:
            log.info("No password specified. Defaulting looking at 'HYDRA_PASSWORD'")

            ret_password = os.environ.get('HYDRA_PASSWORD')

            if password is None:
                ret_password = getpass.getpass()
        else:
            ret_password=password

        return ret_username, ret_password

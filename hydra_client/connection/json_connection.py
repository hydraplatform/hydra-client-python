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

#JSONConnection are synonyums, and used for backward compatibility
__all__ = ['JSONConnection']

import logging
log = logging.getLogger(__name__)

from datetime import datetime
import hydra_base as hb
import six
import collections
from .base_connection import BaseConnection
import json

class JSONConnection(BaseConnection):
    """ Local connection to a Hydra database using hydra_base directly."""
    def __init__(self, *args, **kwargs):
        super(JSONConnection, self).__init__(*args, **kwargs)

        #Hydra Base needs a user ID in its function calls. setting self.user_id
        #allows this client to set this implicitly
        self.user_id = kwargs.get('user_id', None)

        #The user ID can be accessed from the session if it's not set explicitly.
        self.session_id = kwargs.get('session_id', None)
        if self.user_id is None and self.session_id is not None:
            self.user_id = hb.get_session_user(self.session_id)

        if kwargs.get('session') is None:
            db_url = kwargs.get('db_url', None)
            self.autocommit = kwargs.get('autocommit', True)
            hb.db.connect(db_url)

    def call(self, func_name, *args, **kwargs):
        func = getattr(hb, func_name)

        # Add user_id to the kwargs if not given and logged in.
        if 'user_id' not in kwargs and self.user_id is not None:
            kwargs['user_id'] = self.user_id
        else:
            self.login()

        # Convert the arguments to JSON objects
        json_obj_args = list(self.args_to_json_object(*args))

        try:
            ret = func(*json_obj_args, **kwargs)
        except Exception as e:
            hb.db.DBSession.rollback()
            hb.rollback_transaction()
            raise

        # Call the HB function

        try:
            json_resp = list(self.args_to_json_object(ret))
        except ValueError as e:
            log.warning(e)
            json_resp = [ret]

        for o in json_resp:
            if self.autocommit is True:
                try:
                    hb.commit_transaction()
                except Exception as e:
                    hb.db.DBSession.rollback()
                    hb.rollback_transaction()
            return o

    def connect(self):
        try:
            hb.util.hdb.create_default_users_and_perms()
            hb.util.hdb.create_default_units_and_dimensions()
            hb.util.hdb.make_root_user()
            hb.util.hdb.create_default_net()
            hb.commit_transaction()
        except:
            hb.rollback_transaction()

    def login(self, username=None, password=None):

        parsed_username, parsed_password = self.get_username_and_password(username, password)

        self.user_id, self.session_id = hb.login(parsed_username, parsed_password)

        return self.user_id, self.session_id

    def logout(self):

        hb.logout(self.session_id)
        self.user_id, self.session_id = None, None

        return 'OK'

    def args_to_json_object(self, *args):
        for arg in args:
            if arg is None:
                yield None
            elif isinstance(arg, six.string_types):
                yield arg
            elif isinstance(arg, (int, float)):
                yield arg
            elif isinstance(arg, datetime):
                #yield arg
                yield datetime.strftime(arg, self.dateformat)
            elif isinstance(arg, hb.JSONObject):
                yield arg
            elif isinstance(arg, collections.Mapping):
                yield hb.JSONObject(arg)
            elif isinstance(arg, collections.Iterable):
                arg = list(arg) ## in case it's a set or something that doesnt support indexing
                if len(arg) > 0 and isinstance(arg[0], (six.string_types, int, float, datetime)):
                    json_friendly_arg = []
                    for a in arg:
                        if isinstance(a, datetime):
                            json_friendly_arg.append(datetime.strftime(a, self.dateformat))
                        else:
                            json_friendly_arg.append(a)
                    yield json_friendly_arg
                elif len(arg) > 0 and isinstance(arg[0], hb.JSONObject):
                    yield arg
                else:
                    yield [hb.JSONObject(v) for v in arg]
            else:
                yield hb.JSONObject(arg)

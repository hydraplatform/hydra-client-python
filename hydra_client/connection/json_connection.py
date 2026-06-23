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

__all__ = ['JSONConnection']

import logging
log = logging.getLogger(__name__)

from datetime import datetime
import six
import collections
from .base_connection import BaseConnection


class JSONConnection(BaseConnection):
    """ Local connection to a Hydra database using hydra_base directly."""
    def __init__(self, *args, **kwargs):
        # Defer hydra_base import so it is an indirect (optional) requirement.
        import hydra_base as hb
        self._hb = hb

        super(JSONConnection, self).__init__(*args, **kwargs)

        self.user_id = kwargs.get('user_id', None)
        self.db_url = None
        self.session_id = kwargs.get('session_id', None)
        self.autocommit = kwargs.get('autocommit', True)

        if self.user_id is None and self.session_id is not None:
            self.user_id = hb.get_session_user(self.session_id)

        if kwargs.get('session') is None:
            self.db_url = kwargs.get('db_url', None)
            self.db_url = hb.db.connect(self.db_url)

    def call(self, func_name, *args, **kwargs):
        hb = self._hb
        func = getattr(hb, func_name)

        if 'user_id' not in kwargs and self.user_id is not None:
            kwargs['user_id'] = self.user_id
        else:
            self.login()

        json_obj_args = list(self.args_to_json_object(*args))

        k = list(kwargs.keys())
        v = list(self.args_to_json_object(*list(kwargs.values())))
        json_obj_kwargs = {k[i]: v[i] for i in range(len(v))}

        try:
            ret = func(*json_obj_args, **json_obj_kwargs)
        except Exception:
            hb.db.DBSession.rollback()
            hb.rollback_transaction()
            raise

        try:
            json_resp = list(self.args_to_json_object(ret))
        except ValueError as e:
            log.warning(e)
            json_resp = [ret]

        for o in json_resp:
            if self.autocommit is True:
                try:
                    hb.commit_transaction()
                except Exception:
                    hb.db.DBSession.rollback()
                    hb.rollback_transaction()
                    raise
                finally:
                    hb.db.close_session()
                    hb.db.engine.dispose()
            return o

    def connect(self):
        hb = self._hb
        try:
            hb.util.hdb.create_default_users_and_perms()
            hb.util.hdb.create_default_units_and_dimensions()
            hb.util.hdb.make_root_user()
            hb.util.hdb.create_default_net()
            hb.commit_transaction()
        except Exception:
            hb.rollback_transaction()

    def close_session(self):
        self._hb.db.close_session()
        self._hb.db.engine.dispose()

    def login(self, username=None, password=None):
        parsed_username, parsed_password = self.get_username_and_password(username, password)
        self.user_id, self.session_id = self._hb.login(parsed_username, parsed_password)
        return self.user_id, self.session_id

    def logout(self):
        self._hb.logout(self.session_id)
        self.user_id, self.session_id = None, None
        return 'OK'

    def args_to_json_object(self, *args):
        hb = self._hb
        for arg in args:
            if arg is None:
                yield None
            elif isinstance(arg, six.string_types):
                yield arg
            elif isinstance(arg, (int, float)):
                yield arg
            elif isinstance(arg, datetime):
                yield datetime.strftime(arg, self.dateformat)
            elif isinstance(arg, hb.JSONObject):
                yield arg
            elif isinstance(arg, collections.abc.Mapping):
                yield hb.JSONObject(arg)
            elif isinstance(arg, collections.abc.Iterable):
                arg = list(arg)
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

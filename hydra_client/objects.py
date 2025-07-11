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

import six
import enum

from datetime import datetime

def get_json_as_string(json_string_or_dict):
    """
        Take a dict or string and return a string.
        The dict will be json dumped.
        The string will json parsed to check for json validity. In order to deal
        with strings which have been json encoded multiple times, keep json decoding
        until a dict is retrieved or until a non-json structure is identified.
    """

    if isinstance(json_string_or_dict, dict):
        return json.dumps(json_string_or_dict)

    if(isinstance(json_string_or_dict, six.string_types)):
        try:
            return get_json_as_string(json.loads(json_string_or_dict))
        except:
            return json_string_or_dict

def get_json_as_dict(json_string_or_dict):
    """
        Take a dict or string and return a dict if the data is json-encoded.
        The string will json parsed to check for json validity. In order to deal
        with strings which have been json encoded multiple times, keep json decoding
        until a dict is retrieved or until a non-json structure is identified.
    """

    if isinstance(json_string_or_dict, dict):
        return json_string_or_dict

    if(isinstance(json_string_or_dict, six.string_types)):
        try:
            return get_json_as_dict(json.loads(json_string_or_dict))
        except:
            return json_string_or_dict
        
class ExtendedDict(dict):
    """
        A dictionary object whose attributes can be accesed via a '.'.
        Pass in a nested dictionary, a SQLAlchemy object or a JSON string.
    """
    def __init__(self, obj_dict={}, parent=None, extras={}, normalize=True):

        if normalize:
            obj = self.normalise_input(obj_dict)
        else:
            obj = obj_dict

        for k in obj:
            v = obj[k]
            if k == "value_ref":
                continue

            if isinstance(v, ExtendedDict):
                self[k] = v
            elif k == 'layout':
                #Layout is often valid JSON, but we dont want to treat it as a JSON object necessarily
                dict_layout = get_json_as_dict(v)
                self[k] = dict_layout
            elif isinstance(v, dict):
                #TODO what is a better way to identify a dataset?
                if 'unit_id' in v or 'unit' in v or 'metadata' in v or 'type' in v:
                    self[k] = Dataset(v, obj_dict)
                #The value on a dataset should remain untouched
                elif k == 'value':
                    self[k] = v
                else:
                    self[k] = ExtendedDict(v, obj_dict, normalize=normalize)
            elif isinstance(v, list):
                #another special case for datasets, to convert a metadata list into a dict
                if k == 'metadata' and obj_dict is not None:
                    if hasattr(obj_dict, 'get_metadata_as_dict'):
                        self[k] = ExtendedDict(obj_dict.get_metadata_as_dict())
                    else:
                        metadata_dict = ExtendedDict()
                        if hasattr(obj_dict, 'get'):#special case for resource data and row proxies
                            for m in obj_dict.get('metadata', []):
                                metadata_dict[m.key] = m.value
                        self[k] = metadata_dict

                else:
                    is_list_of_objects = True
                    if len(v) > 0:
                        if isinstance(v[0], (float, int)):
                            is_list_of_objects = False
                        elif isinstance(v[0], six.string_types) and len(v[0]) == 0:
                            is_list_of_objects = False
                        elif isinstance(v[0], six.string_types) and v[0][0] not in VALID_JSON_FIRST_CHARS:
                            is_list_of_objects=False

                    if is_list_of_objects is True:
                        l = [ExtendedDict(item, obj_dict) for item in v]
                    else:
                        l = v

                    self[k] = l
            #Special case for SQLAlchemy objects, to stop them recursing up and down
            elif hasattr(v, '_sa_instance_state')\
                    and v._sa_instance_state is not None\
                    and v != parent\
                    and hasattr(obj_dict, '_parents')\
                    and obj_dict._parents is not None\
                    and v.__tablename__ not in obj_dict._parents:
                if v.__tablename__.lower() == 'tdataset':
                    l = Dataset(v, obj_dict)
                else:
                    l = ExtendedDict(v, obj_dict)
                self[k] = l
            #Special case for SQLAlchemy objects, to stop them recursing up and down
            elif hasattr(v, '_sa_instance_state')\
                    and v._sa_instance_state is not None\
                    and v != parent\
                    and hasattr(obj_dict, '_parents')\
                    and obj_dict._parents is not None\
                    and v.__tablename__ in obj_dict._parents:
                continue
            elif isinstance(v, enum.Enum):
                self[k] = v.value
            else:

                if k == '_sa_instance_state':
                    continue

                if parent is not None and type(v) == type(parent):
                    continue

                if isinstance(v, str) and v.replace('.', '', 1).isdigit():
                    v = float(v) if '.' in v else int(v)

                try:
                    if not isinstance(v, int):
                        v = float(v)
                except:
                    pass

                if isinstance(v, datetime):
                    v = six.text_type(v)

                self[six.text_type(k)] = v

        for k, v in extras.items():
            self[k] = v

    def normalise_input(self, obj_dict):
        """
            Pre-process the input dict to ensure that it is compatible with a ExtendedDict
        """
        asdict_fn = getattr(obj_dict, "asdict", None)
        if asdict_fn is not None and callable(asdict_fn):
            rd = obj_dict.asdict()
            for k, v in rd.items():
                self[k] = v

        if isinstance(obj_dict, str):
            try:
                obj = json.loads(obj_dict)
                assert isinstance(obj, dict), "JSON string does not evaluate to a dict"
            except (AssertionError, json.decoder.JSONDecodeError) as e:
                log.critical("Error with value: %s" , obj_dict)
                log.critical(parent)
                raise ValueError("Unable to read string value. Make sure it's JSON serialisable") from e
        elif hasattr(obj_dict, '_asdict') and obj_dict._asdict is not None:
            """
            The argument is a SQLAlchemy object. This originated from a
            Class.column query so there was no instance to trigger the
            value descriptor's __get__ and the external lookup must be
            performed here.
            """
            obj = obj_dict._asdict()
            if obj.get("value") is not None:
                try:
                    """
                    ref_key may be not None but also not a valid oid string, so
                    must handle InvalidId from ObjectId and possible TypeError
                    if oid inst is created but then matches no document.
                    """
                    oid = ObjectId(obj["value"])
                    doc = mongo.get_document_by_oid_inst(oid)
                    obj["value"] = doc["value"]
                except (TypeError, InvalidId):
                    """ The value wasn't an valid ObjectID, keep the current value """
                    pass
        elif hasattr(obj_dict, '__dict__') and len(obj_dict.__dict__) > 0:
            obj = obj_dict.__dict__
            """
            Handle indirect references.
            The sqlalchemy attr "value_ref" is in the instance __dict__
            but the "value" descriptor class attr is not.
            The "value_ref" must remain present in the __dict__ for
            later external db lookup, but should not be present in the
            returned object whereas the "value" should.
            """
            if "value_ref" in obj:
                if obj_dict.value:
                    obj["value"] = obj_dict.value
        elif isinstance(obj_dict, dict):
            """
            The argument is a dict of uncertain provenance. This can
            originate from SQLAlchemy row._asdict() so must be
            handled similarly.
            """
            obj = obj_dict
            ref_key = obj.get("value")
            if ref_key:
                try:
                    oid = ObjectId(ref_key)
                    doc = mongo.get_document_by_oid_inst(oid)
                    obj["value"] = doc["value"]
                except (TypeError, InvalidId):
                    """ The value wasn't an valid ObjectID, keep the current value """
                    pass
        else:
            #last chance...try to cast it as a dict. Do this for sqlalchemy result proxies.
            try:
                obj = dict(obj_dict)
            except:
                log.critical("Error with value: %s" , obj_dict)
                raise ValueError("Unrecognised value. It must be a valid JSON dict, a SQLAlchemy result or a dictionary.")
        return obj

    def __getattr__(self, name):
        # Make sure that "special" methods are returned as before.

        # Keys that start and end with "__" won't be retrievable via attributes
        if name == '__table__':#special case for SQLAlchemy objects
            return self.get('__table__')
        elif name.startswith('__') and name.endswith('__'):
            return super(ExtendedDict, self).__getattr__(name)
        else:
            return self.get(name, None)

    def __setattr__(self, key, value):
        self[key] = value

    def as_json(self):

        return json.dumps(self)

    def get_layout(self):
        """
            Return the 'layout' attribute as a json string
            this is a shorcut for backward compatibility.
            calls the `get_json("layout")` function internally

        """
        return self.get_json('layout')

    def get_json(self, key):
        """
            General function to take an attribute of the object, such as
            layout or app data, which is expected to be in JSON format, and
            return it as a JSON blob,

        """
        if self.get(key) is not None:
            return get_json_as_string(self[key])
        else:
            return None

    #Only for type attrs. How best to generalise this?
    def get_properties(self):
        if self.get('properties') and self.get('properties') is not None:
            return six.text_type(self.properties)
        else:
            return None

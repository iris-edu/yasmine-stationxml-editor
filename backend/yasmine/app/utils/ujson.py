# ****************************************************************************
#
# This file is part of the yasmine editing tool.
#
# yasmine (Yet Another Station Metadata INformation Editor), a tool to
# create and edit station metadata information in FDSN stationXML format,
# is a common development of IRIS and RESIF.
# Development and addition of new features is shared and agreed between * IRIS and RESIF.
#
#
# Version 1.0 of the software was funded by SAGE, a major facility fully
# funded by the National Science Foundation (EAR-1261681-SAGE),
# development done by ISTI and led by IRIS Data Services.
# Version 2.0 of the software was funded by CNRS and development led by * RESIF.
#
# NRLv2 online support (2026): ASGSR, Alexey Emanov.
#
# This program is free software; you can redistribute it
# and/or modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version. *
# This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License (GNU-LGPL) for more details. *
# You should have received a copy of the GNU Lesser General Public
# License along with this software. If not, see
# <https://www.gnu.org/licenses/>
#
#
# 2019/10/07 : version 2.0.0 initial commit
# 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
#
# ****************************************************************************/


# -*- coding: utf-8 -*-
from datetime import datetime, date
import json

import jsonpickle
import jsonpickle.ext.numpy as jsonpickle_numpy
import obspy
from jsonpickle.unpickler import Unpickler
from obspy.core.utcdatetime import UTCDateTime

from yasmine.app.settings import DATE_FORMAT_SYSTEM
from yasmine.app.utils.date import parse_naive_datetime, parse_utcdatetime

ALLOWED_PY_OBJECTS = {
    'obspy.core.inventory.util.ExternalReference',
    'obspy.core.inventory.util.Site',
    'obspy.core.inventory.util.Equipment',
    'obspy.core.inventory.util.Operator',
    'obspy.core.inventory.util.PhoneNumber',
    'obspy.core.inventory.util.Person',
    'obspy.core.inventory.util.Comment',
    'obspy.core.utcdatetime.UTCDateTime',
}


def _is_allowed_py_object(name):
    if not isinstance(name, str):
        return False
    if name in ALLOWED_PY_OBJECTS:
        return True
    return name.startswith('obspy.core.inventory.') or name.startswith('numpy.')


jsonpickle_numpy.register_handlers()


class JSONEncoder(json.JSONEncoder):

    ''' Class to encode JSON format send to frontend.'''

    def encode_date(self, date):
        return date.strftime(DATE_FORMAT_SYSTEM)

    def _stringify_utcdatetimes(self, obj, seen=None):
        """Replace nested UTCDateTime values with ISO-8601 strings in place.

        encode_complex_obj previously only converted dates on the top-level object,
        so nested values (e.g. DataAvailability.spans[*].start/end) were left as
        jsonpickle UTCDateTime py/state blobs the frontend could not parse.
        """
        if seen is None:
            seen = set()
        obj_id = id(obj)
        if obj_id in seen or not hasattr(obj, '__dict__'):
            return
        seen.add(obj_id)

        for attr, value in list(obj.__dict__.items()):
            if isinstance(value, (UTCDateTime, datetime, date)):
                setattr(obj, attr, self.encode_date(
                    value.datetime if isinstance(value, UTCDateTime) else value
                ))
            elif isinstance(value, list):
                new_list = []
                for item in value:
                    if isinstance(item, (UTCDateTime, datetime, date)):
                        new_list.append(self.encode_date(
                            item.datetime if isinstance(item, UTCDateTime) else item
                        ))
                    else:
                        if item is not None and obspy.__name__ in getattr(item, '__module__', ''):
                            self._stringify_utcdatetimes(item, seen)
                        new_list.append(item)
                setattr(obj, attr, new_list)

    def encode_complex_obj(self, obj):
        self._stringify_utcdatetimes(obj)

        def convert(key):
            return key.replace('_', '', 1) if key.find('_') == 0 else key

        response = json.loads(jsonpickle.dumps(obj, make_refs=False))
        return self.change_keys(response, convert)

    def change_keys(self, obj, convert):
        if isinstance(obj, (str, int, float)):
            return obj
        if isinstance(obj, dict):
            new = obj.__class__()
            for k, v in obj.items():
                new[convert(k)] = self.change_keys(v, convert)
        elif isinstance(obj, (list, set, tuple)):
            new = obj.__class__(self.change_keys(v, convert) for v in obj)
        else:
            return obj
        return new

    def default(self, obj):
        # to format date
        if isinstance(obj, datetime) or isinstance(obj, date):
            encoded_object = self.encode_date(obj)
        elif isinstance(obj, UTCDateTime):
            encoded_object = self.encode_date(obj.datetime)
        elif obspy.__name__ in getattr(obj, '__module__', ''):
            encoded_object = self.encode_complex_obj(obj)
        else:
            encoded_object = json.JSONEncoder.default(self, obj)
        return encoded_object


class JSONDecoder(json.JSONDecoder):

    ''' Class to decode JSON format received from frontend.'''

    def decode_date(self, value):
        if isinstance(value, list):
            res = []
            for v in value:
                res.append(self._parse_date(v))
            return res
        return self._parse_date(value)

    def _parse_date(self, value):
        """Parse an ISO-8601 string that ObsPy UTCDateTime accepts."""
        if not value or value == '':
            return None
        return parse_utcdatetime(value)

    def decode_complex_obj(self, pairs):
        res_dict = {}
        for k, v in pairs:
            if k.endswith('_date') or k.endswith('_time'):
                v = self.decode_date(v)
            res_dict[k] = v
        py_object = res_dict.get('py/object')
        if not _is_allowed_py_object(py_object):
            raise ValueError('Unsupported object type: %s' % py_object)
        context = Unpickler()
        res = context.restore(res_dict, reset=True)

        return res

    def decode_simple_obj(self, pairs):
        obj = {}
        for key, value in pairs:
            if isinstance(value, str) and key in ['created_at', 'updated_at', 'start_date', 'end_date']:
                try:
                    parsed = parse_naive_datetime(value)
                except (TypeError, ValueError):
                    obj[key] = value
                else:
                    obj[key] = parsed
            else:
                obj[key] = value
        return obj

    def __init__(self, *args, **kwargs):

        def decode_hook(pairs):
            """Load with dates"""
            obj = None
            if 'py/object' in [x[0] for x in pairs]:
                obj = self.decode_complex_obj(pairs)
            else:
                obj = self.decode_simple_obj(pairs)
            return obj

        kwargs['object_pairs_hook'] = decode_hook
        super(JSONDecoder, self).__init__(*args, **kwargs)

    def decode(self, s):
        obj = super(JSONDecoder, self).decode(s)
        # to handle id returned like minus value from from end for the new records
        if isinstance(obj, dict):
            for key in obj:
                value = obj.get(key)
                if 'id' in key and (
                    value == ''
                    or value == '-1'
                    or (isinstance(value, (int, float)) and not isinstance(value, bool) and value < 0)
                ):
                    obj[key] = None

        return obj


def json_load(data, cls=JSONDecoder):
    return json.loads(data, cls=cls)


def json_dump(data, cls=JSONEncoder):
    return json.dumps(data, cls=cls)

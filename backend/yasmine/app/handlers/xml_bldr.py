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
# 2026-09-27, version 4.4.0-beta: ASGSR, Alexey Emanov
#
# ****************************************************************************/


import json
import os
import time

from sqlalchemy import and_
from sqlalchemy.orm import joinedload
import tornado.gen
import tornado.httpclient
from tornado.web import HTTPError

from yasmine.app.enums.xml_node import XmlNodeEnum, XmlNodeAttrEnum
from yasmine.app.exceptions.exceptions import BusinessException
from yasmine.app.handlers.base import ExtJsHandler, BaseHandler, AsyncThreadMixin
from yasmine.app.handlers.equipment import EquipmentMixin
from yasmine.app.models import XmlNodeInstModel, XmlNodeAttrValModel, XmlNodeAttrModel, XmlNodeAttrRelationModel
from yasmine.app.services.attribute_service import AttributeService
from yasmine.app.services.node_service import NodeService
from yasmine.app.settings import TMP_ROOT
from yasmine.app.services.strict_validation_job import (
    get_strict_validation,
    start_strict_validation,
)
from yasmine.app.services.xml_service import XmlService
from yasmine.app.utils.date import parse_naive_datetime
from yasmine.app.utils.inv_valid import VALIDATION_RULES
from yasmine.app.utils.db import db_transaction
from yasmine.app.utils.response_plot import polynomial_or_polezero_response
from yasmine.app.utils.stationxml_codec import (
    MEASURED_ATTRIBUTE_NAMES,
    measured_metadata_payload,
)
from yasmine.app.utils.ujson import json_load


class XmlValidationHandler(AsyncThreadMixin, BaseHandler):
    def async_get(self, xml_id, *_, **__):
        try:
            result = XmlService(self).validate(xml_id)
        except HTTPError as e:
            raise
        except Exception as e:
            raise HTTPError(reason="Unable to build XML: '%s'" % str(e))
        return {
            'success': len(result['errors']) == 0,
            'errors': result['errors'],
            'warnings': result['warnings'],
            'issues': result['issues'],
        }


class XmlStrictValidationHandler(AsyncThreadMixin, BaseHandler):
    def async_get(self, xml_id, *_, **__):
        job_id = start_strict_validation(self.application, xml_id)
        job = get_strict_validation(job_id)
        payload = job.snapshot() if job is not None else {
            'success': False,
            'percent': 0,
            'done': True,
            'failed': True,
            'message': 'Strict XML check could not be started.',
        }
        payload['job_id'] = job_id
        return payload


class XmlStrictValidationProgressHandler(AsyncThreadMixin, BaseHandler):
    def async_get(self, job_id, *_, **__):
        job = get_strict_validation(job_id)
        if job is None:
            return {
                'success': False,
                'percent': 0,
                'done': True,
                'failed': True,
                'message': 'Strict XML check is no longer running. Start it again.',
            }
        return job.snapshot()


class XmlNodePathHandler(AsyncThreadMixin, BaseHandler):
    def async_get(self, *_, **__):
        try:
            inst_id = int(self.get_argument('nodeId'))
        except (TypeError, ValueError):
            return {'success': False, 'message': 'Node not found'}
        path = []
        if inst_id > 0:
            node = self.db.get(XmlNodeInstModel, inst_id)
            if node is None:
                return {'success': False, 'message': 'Node not found'}
            self._get_parent(node, path)
            path.reverse()
        return {'success': True, 'data': {'path': path}}

    def _get_parent(self, node, result):
        if node is None:
            return
        code_attr = node.attr_vals.join(XmlNodeAttrValModel.attr) \
            .filter(XmlNodeAttrModel.name == XmlNodeAttrEnum.CODE) \
            .first()
        code = code_attr.value_obj if code_attr is not None else None
        result.append({'id': node.id, 'code': code, 'nodeType': node.node_id})
        if not (node.parent_id is None):
            self._get_parent(node.parent, result)


def find_similar_channel(channels, channel_code, location_code, station_code, skip_id=None):
    """Return (node id, has response) for the first channel with the same code, location, and station.

    Response is detected on its own, so attribute order does not matter, and a
    response on an earlier non-matching channel does not leak into the match.
    """
    for current_channel in channels:
        if skip_id is not None and current_channel.id == skip_id:
            continue
        code_found = False
        location_found = False
        has_response = False
        for attr_val in current_channel.attr_vals:
            name = attr_val.attr.name
            if name == XmlNodeAttrEnum.CODE and attr_val.value_obj == channel_code:
                code_found = True
            elif name == XmlNodeAttrEnum.LOCATION_CODE and attr_val.value_obj == location_code:
                location_found = True
            elif name == XmlNodeAttrEnum.RESPONSE:
                has_response = True
        parent = current_channel.parent
        if (
            code_found and location_found and parent is not None
            and parent.code == station_code
        ):
            return current_channel.id, has_response
    return None, False


class XmlSimilarChannelHandler(AsyncThreadMixin, BaseHandler):
    def async_get(self, *_, **__):
        try:
            target_xml_id = int(self.get_argument('xmlId'))
            channel_id = int(self.get_argument('nodeInstanceId'))
        except (TypeError, ValueError):
            return {'success': False, 'message': 'Channel not found'}
        channel = self.db.get(XmlNodeInstModel, channel_id)
        if channel is None or channel.parent is None:
            return {'success': False, 'message': 'Channel not found'}
        station_code = channel.parent.code
        code_attr = channel.attr_vals.join(XmlNodeAttrValModel.attr) \
            .filter(XmlNodeAttrModel.name == XmlNodeAttrEnum.CODE) \
            .first()
        loc_attr = channel.attr_vals.join(XmlNodeAttrValModel.attr) \
            .filter(XmlNodeAttrModel.name == XmlNodeAttrEnum.LOCATION_CODE) \
            .first()
        if code_attr is None or loc_attr is None:
            return {'success': False, 'message': 'Channel code or location is missing'}
        channel_code = code_attr.value_obj
        channel_location_code = loc_attr.value_obj

        channels = self.db.query(XmlNodeInstModel) \
            .filter(XmlNodeInstModel.node_id == XmlNodeEnum.CHANNEL) \
            .filter(XmlNodeInstModel.xml_id == target_xml_id) \
            .all()

        similar_channel_id, has_response = find_similar_channel(
            channels,
            channel_code,
            channel_location_code,
            station_code,
            skip_id=channel.id,
        )
        return {'success': True, 'data': {'nodeInstanceId': similar_channel_id, 'hasResponse': has_response}}


class XmlEpochHandler(AsyncThreadMixin, BaseHandler):
    def async_get(self, xml_id, *_, **__):
        dates = self.db \
            .query(XmlNodeInstModel.start_date) \
            .filter(and_(XmlNodeInstModel.xml_id == xml_id, XmlNodeInstModel.start_date.isnot(None))) \
            .distinct() \
            .order_by(XmlNodeInstModel.start_date.desc()) \
            .all()
        return list(map(lambda x: {'date': x[0]}, dates))


class XmlNodeHandler(AsyncThreadMixin, BaseHandler):
    def async_get(self, xml_id, node_id, *_, **__):
        filters = self.request_params.get('filter', None)
        return NodeService(self).load_node_from_xml(xml_id, node_id, filters)

    def async_post(self, xml_id, *_, **__):
        params = self.request_params or {}
        node_inst_id = params.get('node_inst_id', None)
        parent_id = params.get('parentId')
        node_type = params.get('nodeType')
        if node_type is None:
            raise HTTPError(400, reason='nodeType is required')
        node_service = NodeService(self)
        parent_id = None if parent_id in (None, '', 0, '0') else parent_id
        try:
            if int(node_inst_id or 0) == 0:
                new_node_id = node_service.create_default_node_for_xml(xml_id, node_type, parent_id)
            else:
                new_node_id = node_service.add_node_to_xml(xml_id, int(node_inst_id), parent_id)
        except BusinessException as err:
            return {'success': False, 'message': str(err)}
        except (TypeError, ValueError):
            return {'success': False, 'message': 'Invalid node id'}
        return {'success': True, 'data': {'nodeId': new_node_id}}

    def async_delete(self, xml_id, node_id, *_, **__):
        NodeService(self).delete_node_from_xml(xml_id, node_id)
        return {'success': True}


class XmlNodeExtensionsHandler(AsyncThreadMixin, BaseHandler):
    """GET /api/xml/extensions/<xml_id>/<node_id>/ - read-only foreign-namespace summary."""

    def async_get(self, xml_id, node_id, *_, **__):
        summary = NodeService(self).extension_summary_for_node(
            node_id, xml_id=xml_id
        )
        if summary is None:
            return {'success': False, 'message': 'Invalid node id'}
        return {'success': True, 'data': summary}


class XmlNodeAttrHandler(EquipmentMixin, ExtJsHandler):
    model = XmlNodeAttrValModel
    send_total_count = False
    response_xml_str = ''

    def get_data_query(self):
        return self.db.query(XmlNodeAttrValModel) \
            .join(XmlNodeAttrValModel.attr) \
            .join(XmlNodeAttrModel.widget) \
            .options(joinedload(XmlNodeAttrValModel.attr).joinedload(XmlNodeAttrModel.widget)) \
            .options(joinedload(XmlNodeAttrValModel.node_inst))

    def determine_fields(self, *_, **__):
        return [
            'id',
            'attr_name',
            'attr_class',
            'value_obj',
            'value_meta',
            'attr_id',
            'node_inst_id',
            'attr_index',
            'node_type_id',
        ]

    def serialize(self, q_object, fields):
        resp = super(XmlNodeAttrHandler, self).serialize(q_object, fields)
        value_obj = resp['value_obj']
        if q_object.attr.name == 'response':
            resp['value_obj'] = polynomial_or_polezero_response(value_obj)
        elif q_object.attr.name in MEASURED_ATTRIBUTE_NAMES:
            resp['value_meta'] = measured_metadata_payload(value_obj)
        _, _, _, required = self.application.config.get_cfg_by_node_id(q_object.node_inst.node_id)
        resp['required'] = q_object.attr_name in required

        return resp

    def create_obj(self):
        attr_id = self.request_params.get('attr_id') or self.request_params.get('parameterId')
        node_id = self.request_params.get('node_inst_id') or self.request_params.get('nodeId')
        if not attr_id or not node_id:
            raise ValueError('attr_id and node_inst_id are required when creating an attribute')
        try:
            attr_id = int(attr_id)
        except (TypeError, ValueError):
            raise ValueError('attr_id must be a valid integer')
        if attr_id <= 0:
            raise ValueError('attr_id must be a positive integer')
        attr = self.db.get(XmlNodeAttrModel, attr_id)
        if attr is None:
            raise ValueError('Attribute with id %s does not exist' % attr_id)
        return AttributeService(self).create_attribute(
            attribute_id=attr_id,
            node_id=node_id,
            value=self.request_params['value_obj'],
            spread_to_channels=json_load(self.get_argument('spread_to_channels', 'null')),
            value_meta=self.request_params.get('value_meta'),
        )

    def update_obj(self, obj):
        AttributeService(self).update_attribute(
            attr_model=obj,
            value=self.request_params['value_obj'],
            spread_to_channels=json_load(self.get_argument('spread_to_channels', 'null')),
            value_meta=(
                self.request_params['value_meta']
                if 'value_meta' in self.request_params
                else AttributeService.UNSET
            ),
        )

    def async_post(self, *_, **__):
        try:
            return super(XmlNodeAttrHandler, self).async_post(*_, **__)
        except BusinessException as err:
            return {'success': False, 'message': str(err), 'data': str(err)}

    def async_put(self, db_id, **kwargs):
        try:
            return super(XmlNodeAttrHandler, self).async_put(db_id, **kwargs)
        except Exception as e:
            self.set_status(500)
            err_msg = str(e)
            return {'success': False, 'data': err_msg, 'message': err_msg}

    def async_delete(self, db_id, **__):
        try:
            with db_transaction(self.db):
                AttributeService(self).delete_attribute(db_id)
        except BusinessException as err:
            return {'success': False, 'message': str(err)}
        return {'success': True}


class XmlNodeAvailableAttrHandler(AsyncThreadMixin, BaseHandler):

    def serialize_attr(self, attr):
        return {
            'id': attr.id,
            'name': attr.name,
            'class': attr.widget.name
        }

    def async_get(self, node_id, *_, **__):
        data = []

        node_inst = self.db.get(XmlNodeInstModel, node_id)
        if node_inst is None:
            return []

        set_attrs = self.db.query(XmlNodeAttrValModel.attr_id) \
            .filter(XmlNodeAttrValModel.node_inst_id == node_inst.id)

        node_attrs = self.db.query(XmlNodeAttrRelationModel) \
            .join(XmlNodeAttrRelationModel.attr) \
            .join(XmlNodeAttrModel.widget) \
            .options(joinedload(XmlNodeAttrRelationModel.attr).joinedload(XmlNodeAttrModel.widget)) \
            .filter(XmlNodeAttrRelationModel.node_id == node_inst.node_id) \
            .filter(XmlNodeAttrModel.id.notin_(set_attrs)) \
            .all()

        for node_attr in node_attrs:
            data.append(self.serialize_attr(node_attr.attr))

        return data


class XmlNodeAttrValidateHandler(AsyncThreadMixin, BaseHandler):
    @property
    def request_params(self):
        """Use standard JSON parsing - validation does not need ObsPy object decoding."""
        if not hasattr(self, '_validate_params_cache'):
            try:
                self._validate_params_cache = json.loads(self.request.body or '{}')
            except (ValueError, TypeError):
                self._validate_params_cache = {}
        return self._validate_params_cache

    def async_post(self, *_, **__):
        try:
            params = self.request_params or {}
        except Exception:
            return {'success': False, 'message': ['Invalid request body']}
        node_id = params.get('node_id')
        attr_name = params.get('attr_name')
        if node_id is None or attr_name is None:
            return {'success': False, 'message': ['node_id and attr_name are required']}
        try:
            node_id = int(node_id)
        except (TypeError, ValueError):
            return {'success': False, 'message': ['node_id must be a valid integer']}
        value = params.get('value', None)
        only_critical = params.get('only_critical', False)

        rules = VALIDATION_RULES.get(node_id, {}).get(attr_name, [])
        messages = []
        for rule in rules:
            if not only_critical or rule.critical:
                try:
                    res = rule.validate(value)
                    if res is not True:
                        messages.append(res)
                except Exception:
                    messages.append('Validation error')
        return {'success': True, 'message': messages}


class XmlMapHandler(AsyncThreadMixin, BaseHandler):
    def async_get(self, xml_id, *_, **__):
        node_id = self.get_argument('nodeId', '0')
        epoch_raw = self.get_argument('epoch', '')
        epoch = None
        if epoch_raw not in ('', 'null'):
            try:
                epoch = parse_naive_datetime(epoch_raw)
            except ValueError:
                return {'success': False, 'message': 'Invalid epoch'}
        include_channels = self.get_argument('channels', '') in ('1', 'true', 'yes')
        data = NodeService(self).load_map(
            xml_id, node_id, epoch, include_channels=include_channels
        )
        if data is None:
            return {'success': False, 'message': 'Node not found'}
        return {'success': True, 'data': data}


_TILE_URLS = {
    'osm': 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    'opentopomap': 'https://tile.opentopomap.org/{z}/{x}/{y}.png',
}
_TILE_USER_AGENT = 'Yasmine-StationXML-Editor (local station map)'
_TILE_CACHE_MAX_AGE = 86400


def tile_cache_path(source, z, x, y, root=None):
    base = root or os.path.join(TMP_ROOT, 'map-tiles')
    return os.path.join(base, source, str(int(z)), str(int(x)), '%s.png' % int(y))


def read_cached_tile(path, max_age=_TILE_CACHE_MAX_AGE, now=None):
    try:
        modified = os.path.getmtime(path)
    except OSError:
        return None
    moment = time.time() if now is None else now
    if moment - modified > max_age:
        return None
    with open(path, 'rb') as handle:
        return handle.read()


def write_cached_tile(path, body):
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    temporary = '%s.%s.part' % (path, os.getpid())
    with open(temporary, 'wb') as handle:
        handle.write(body)
    os.replace(temporary, path)


class MapTileHandler(BaseHandler):
    @tornado.gen.coroutine
    def get(self, source, z, x, y, *args, **kwargs):
        template = _TILE_URLS.get(source)
        try:
            zi, xi, yi = int(z), int(x), int(y)
        except (TypeError, ValueError):
            zi = xi = yi = -1
        if template is None or zi < 0 or zi > 19 or xi < 0 or yi < 0 or xi >= 2 ** zi or yi >= 2 ** zi:
            self.set_status(400)
            self.write({'success': False, 'message': 'Tile unavailable'})
            return
        path = tile_cache_path(source, zi, xi, yi)
        cached = read_cached_tile(path)
        if cached is not None:
            self.set_header('Content-Type', 'image/png')
            self.set_header('Cache-Control', 'public, max-age=86400')
            self.write(cached)
            return
        url = template.format(z=zi, x=xi, y=yi)
        client = tornado.httpclient.AsyncHTTPClient()
        try:
            response = yield client.fetch(
                url,
                headers={'User-Agent': _TILE_USER_AGENT},
                request_timeout=20,
                connect_timeout=10,
            )
        except (tornado.httpclient.HTTPError, OSError):
            self.set_status(502)
            self.write({'success': False, 'message': 'Tile unavailable'})
            return
        content_type = response.headers.get('Content-Type', 'image/png').split(';')[0]
        if content_type.startswith('image/') and response.body:
            try:
                write_cached_tile(path, response.body)
            except OSError:
                pass
        self.set_header('Content-Type', content_type)
        self.set_header('Cache-Control', 'public, max-age=86400')
        self.write(response.body)

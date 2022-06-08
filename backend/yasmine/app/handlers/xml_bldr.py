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
#
# ****************************************************************************/


from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from tornado.web import HTTPError

from yasmine.app.enums.xml_node import XmlNodeEnum, XmlNodeAttrEnum
from yasmine.app.handlers.base import ExtJsHandler, BaseHandler, AsyncThreadMixin
from yasmine.app.handlers.equipment import EquipmentMixin
from yasmine.app.models import XmlNodeInstModel, XmlNodeAttrValModel, XmlNodeAttrModel, XmlNodeAttrRelationModel
from yasmine.app.services.attribute_service import AttributeService
from yasmine.app.services.node_service import NodeService
from yasmine.app.services.xml_service import XmlService
from yasmine.app.utils.imp_exp import ConvertToInventory
from yasmine.app.utils.inv_valid import ValidateInventory, VALIDATION_RULES
from yasmine.app.utils.response_plot import polynomial_or_polezero_response
from yasmine.app.utils.ujson import json_load


class XmlValidationHandler(AsyncThreadMixin, BaseHandler):
    def async_get(self, xml_id, *_, **__):
        try:
            inv = ConvertToInventory(xml_id, self).run()
        except HTTPError as e:
            raise
        except Exception as e:
            raise HTTPError(reason="Unable to build XML: '%s'" % str(e))
        errors = ValidateInventory(inv, self).run()
        errors.extend(XmlService(self).validate(xml_id))
        return errors


class XmlNodePathHandler(AsyncThreadMixin, BaseHandler):
    def async_get(self, *_, **__):
        inst_id = int(self.get_argument('nodeId'))
        path = []
        if inst_id > 0:
            node = self.db.query(XmlNodeInstModel).get(inst_id)
            self._get_parent(node, path)
            path.reverse()
        return {'success': True, 'data': {'path': path}}

    def _get_parent(self, node, result):
        code = node.attr_vals.join(XmlNodeAttrValModel.attr) \
            .filter(XmlNodeAttrModel.name == XmlNodeAttrEnum.CODE) \
            .first().value_obj
        result.append({'id': node.id, 'code': code, 'nodeType': node.node_id})
        if not (node.parent_id is None):
            self._get_parent(node.parent, result)


class XmlSimilarChannelHandler(AsyncThreadMixin, BaseHandler):
    def async_get(self, *_, **__):
        target_xml_id = int(self.get_argument('xmlId'))
        channel_id = int(self.get_argument('nodeInstanceId'))
        channel = self.db.query(XmlNodeInstModel).get(channel_id)
        station_code = channel.parent.code
        channel_code = channel.attr_vals.join(XmlNodeAttrValModel.attr) \
            .filter(XmlNodeAttrModel.name == XmlNodeAttrEnum.CODE) \
            .first().value_obj
        channel_location_code = channel.attr_vals.join(XmlNodeAttrValModel.attr) \
            .filter(XmlNodeAttrModel.name == XmlNodeAttrEnum.LOCATION_CODE) \
            .first().value_obj

        channels = self.db.query(XmlNodeInstModel) \
            .filter(XmlNodeInstModel.node_id == XmlNodeEnum.CHANNEL) \
            .filter(XmlNodeInstModel.xml_id == target_xml_id) \
            .all()

        similar_channel_id = None
        has_response = False
        for current_channel in channels:
            code_found = False
            location_found = False
            for attr_val in current_channel.attr_vals:
                if attr_val.attr.name == XmlNodeAttrEnum.CODE and attr_val.value_obj == channel_code:
                    code_found = True
                if attr_val.attr.name == XmlNodeAttrEnum.LOCATION_CODE and attr_val.value_obj == channel_location_code:
                    location_found = True
                if code_found and location_found and attr_val.attr.name == XmlNodeAttrEnum.RESPONSE:
                    has_response = True
            if code_found and location_found and current_channel.parent.code == station_code:
                similar_channel_id = current_channel.id
                break

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
        params = self.request_params
        node_inst_id = params.get('node_inst_id', None)
        parent_id = params['parentId']
        node_service = NodeService(self)
        if int(node_inst_id) == 0:
            new_node_id = node_service.create_default_node_for_xml(xml_id, params['nodeType'], parent_id)
        else:
            new_node_id = node_service.add_node_to_xml(xml_id, int(node_inst_id), parent_id)
        return {'success': True, 'data': {'nodeId': new_node_id}}

    def async_delete(self, xml_id, node_id, *_, **__):
        NodeService(self).delete_node_from_xml(xml_id, node_id)
        return {'success': True}


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
        return ['id', 'attr_name', 'attr_class', 'value_obj', 'attr_id', 'node_inst_id', 'attr_index', 'node_type_id']

    def serialize(self, q_object, fields):
        resp = super(XmlNodeAttrHandler, self).serialize(q_object, fields)
        value_obj = resp['value_obj']
        if q_object.attr.name == 'response' and value_obj:
            resp['value_obj'] = polynomial_or_polezero_response(value_obj)
        _, _, _, required = self.application.config.get_cfg_by_node_id(q_object.node_inst.node_id)
        resp['required'] = q_object.attr_name in required

        return resp

    def create_obj(self):
        return AttributeService(self).create_attribute(
            attribute_id=self.request_params['attr_id'],
            node_id=self.request_params['node_inst_id'],
            value=self.request_params['value_obj'],
            spread_to_channels=json_load(self.get_argument('spread_to_channels', 'null'))
        )

    def update_obj(self, obj):
        AttributeService(self).update_attribute(
            attr_model=obj,
            value=self.request_params['value_obj'],
            spread_to_channels=json_load(self.get_argument('spread_to_channels', 'null'))
        )

    def async_delete(self, db_id, **__):
        AttributeService(self).delete_attribute(db_id)
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

        node_inst = self.db.query(XmlNodeInstModel).get(node_id)

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
    def async_post(self, *_, **__):
        params = self.request_params
        node_id = params['node_id']
        attr_name = params['attr_name']
        value = params.get('value', None)
        only_critical = params.get('only_critical', False)

        rules = VALIDATION_RULES.get(node_id, {}).get(attr_name, [])
        messages = []
        for rule in rules:
            if not only_critical or rule.critical:
                res = rule.validate(value)
                if res is not True:
                    messages.append(res)
        return {'success': True, 'message': messages}

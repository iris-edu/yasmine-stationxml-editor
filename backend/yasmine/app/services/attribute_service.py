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
import io

from obspy import UTCDateTime
from obspy import read_inventory

from yasmine.app.enums.xml_node import XmlNodeAttrEnum, XmlNodeEnum
from yasmine.app.exceptions.exceptions import ResponseEditException
from yasmine.app.handlers.equipment import EquipmentMixin
from yasmine.app.models import XmlNodeAttrValModel, XmlNodeInstModel, XmlNodeAttrModel
from yasmine.app.services.xml_service import XmlService
from yasmine.app.settings import DATE_FORMAT_SYSTEM
from yasmine.app.utils.date import strptime
from yasmine.app.utils.facade import HandlerMixin
from yasmine.app.utils.imp_exp import ConvertToInventory


class AttributeService(HandlerMixin, EquipmentMixin):
    def create_attribute(self, attribute_id, node_id, value, spread_to_channels):
        attr_model = XmlNodeAttrValModel()
        attr_model.node_inst = self.db.query(XmlNodeInstModel).get(node_id)
        attr_model.attr = self.db.query(XmlNodeAttrModel).get(attribute_id)

        self._update_attribute_value(attr_model, value)
        self._update_node_shortcuts(attr_model, value)

        if spread_to_channels:
            self._spread_value_to_channels(attr_model)

        XmlService(self).update_timestamp(attr_model.node_inst.xml_id)

        return attr_model

    def update_attribute(self, attr_model, value, spread_to_channels):
        self._update_attribute_value(attr_model, value)
        self._update_node_shortcuts(attr_model, value)

        if spread_to_channels:
            self._spread_value_to_channels(attr_model)

        XmlService(self).update_timestamp(attr_model.node_inst.xml_id)

    def delete_attribute(self, db_id):
        attr_model = self.db.query(XmlNodeAttrValModel).get(db_id)
        xml_id = attr_model.node_inst.xml_id
        self._update_node_shortcuts(attr_model, None)

        self.db.query(XmlNodeAttrValModel) \
            .filter(XmlNodeAttrValModel.id == db_id) \
            .delete()

        XmlService(self).update_timestamp(xml_id)

    def _update_attribute_value(self, obj, value):
        if self._is_date_attribute(obj):
            self._update_date_attribute(obj, value)
        elif self._is_edit_response_attribute(obj, value):
            self._update_modified_response(obj, value)
        elif self._is_new_response_attribute(obj, value):
            self._update_new_response(obj, value)
        elif self._is_equipments_attribute(obj):
            self._update_equipment_attribute(obj, value)
        elif self._is_datalogger_or_sensor_attribute(obj):
            self._update_datalogger_or_sensor_attribute(obj, value)
        else:
            obj.value_obj = value.strip() if isinstance(value, str) else value

    def _spread_value_to_channels(self, obj):
        if obj.node_inst.node_id == XmlNodeEnum.STATION:
            channel_attributes = self.db.query(XmlNodeAttrValModel) \
                .join(XmlNodeAttrValModel.node_inst) \
                .filter(XmlNodeAttrValModel.attr_id == obj.attr.id, XmlNodeInstModel.parent_id == obj.node_inst.id) \
                .all()
            for channel_attribute in channel_attributes:
                channel_attribute.value_obj = obj.value_obj
                self._update_node_shortcuts(channel_attribute, obj.value_obj)

    def _update_modified_response(self, obj, value):
        node_id = value['nodeId']
        station_xml = ConvertToInventory(None, self).get_station_xml_for_channel(node_id)
        self.response_xml_str = ''
        self._prepare_response_json_as_xml(value['response'])
        try:
            response = self.get_updated_response_obj(self.response_xml_str, station_xml)
            if not response.instrument_polynomial:
                response.get_sacpz()
            obj.value_obj = response
        except Exception as err:
            raise ResponseEditException(err)

    def _update_new_response(self, obj, value):
        library_type = value['libraryType']
        sensor_keys = value['sensorKeys']
        datalogger_keys = value['dataloggerKeys']
        equipment = self.manage_equipment(obj.node_inst, sensor_keys, datalogger_keys, library_type, obj)
        for attr in equipment:
            if attr is not None:
                self.db.add(attr)

    def _prepare_response_json_as_xml(self, json_obj, parent_node=None):
        for key, value in json_obj.items():
            if key == 'children':
                for item in value:
                    if type(item) == dict:
                        self._prepare_response_json_as_xml(item, parent_node)
                    else:
                        self.response_xml_str += str(item)
            elif key == 'attributes':
                attrs = ''
                for attrKey, attrValue in value.items():
                    if len(str(attrValue)) > 0:
                        if len(attrs) > 0:
                            attrs += ' '
                        attrs += '%s="%s"' % (attrKey, attrValue)
                start = self.response_xml_str.rfind('<%s>' % parent_node)
                end = start + len(parent_node) + 2
                self.response_xml_str = self.response_xml_str[:start] + '<%s %s>' % (
                    parent_node, attrs) + self.response_xml_str[end:]
            else:
                self.response_xml_str += '<%s>' % key
                if type(value) == dict:
                    self._prepare_response_json_as_xml(value, key)
                else:
                    self.response_xml_str += str(value)
                self.response_xml_str += '</%s>' % key

    @staticmethod
    def get_updated_response_obj(response_xml, station_xml):
        resp_start = station_xml.find('<Response>')
        resp_end = station_xml.find('</Response>') + 11
        old_response = station_xml[resp_start:resp_end]
        station_xml = station_xml.replace(old_response, response_xml)
        station_xml_binary = io.BytesIO(station_xml.encode('utf-8'))
        inv = read_inventory(station_xml_binary)
        for network in inv.networks:
            for station in network.stations:
                for channel in station.channels:
                    if hasattr(channel, 'response'):
                        return getattr(channel, 'response')

    def _update_datalogger_or_sensor_attribute(self, obj, equipment):
        self._update_equipment_calibration_date([equipment])
        obj.value_obj = equipment

    def _update_equipment_attribute(self, obj, equipments):
        self._update_equipment_calibration_date(equipments)
        obj.value_obj = equipments

    @staticmethod
    def _update_equipment_calibration_date(equipments):
        for equipment in equipments:
            calibration_dates = []
            for calibration_date in equipment.calibration_dates:
                calibration_dates.append(UTCDateTime(calibration_date))
            equipment.calibration_dates = calibration_dates

    @staticmethod
    def _update_date_attribute(obj, value):
        obj.value_obj = UTCDateTime(strptime(value, DATE_FORMAT_SYSTEM))

    @staticmethod
    def _update_node_shortcuts(obj, value):
        if obj.attr.name in [XmlNodeAttrEnum.CODE]:
            obj.node_inst.code = value
        elif obj.attr.name in [XmlNodeAttrEnum.START_DATE, XmlNodeAttrEnum.END_DATE]:
            py_date = None
            if isinstance(value, str):
                py_date = strptime(value, DATE_FORMAT_SYSTEM)
            elif value is not None:
                py_date = value.datetime
            setattr(obj.node_inst, obj.attr.name, py_date)

    @staticmethod
    def _is_date_attribute(obj):
        return obj.attr.name in [XmlNodeAttrEnum.START_DATE,
                                 XmlNodeAttrEnum.END_DATE,
                                 XmlNodeAttrEnum.CREATION_DATE,
                                 XmlNodeAttrEnum.TERMINATION_DATE]

    @staticmethod
    def _is_equipments_attribute(obj):
        return obj.attr.name in [XmlNodeAttrEnum.EQUIPMENTS]

    @staticmethod
    def _is_datalogger_or_sensor_attribute(obj):
        return obj.attr.name in [XmlNodeAttrEnum.DATA_LOGGER, XmlNodeAttrEnum.SENSOR]

    @staticmethod
    def _is_edit_response_attribute(obj, value):
        return obj.attr.name in [XmlNodeAttrEnum.RESPONSE] and 'response' in value

    @staticmethod
    def _is_new_response_attribute(obj, value):
        return obj.attr.name in [XmlNodeAttrEnum.RESPONSE] and 'response' not in value

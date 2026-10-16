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
# 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
#
# ****************************************************************************/
from obspy.core.inventory.util import (
    Azimuth,
    ClockDrift,
    DataAvailability,
    DataAvailabilitySpan,
    Dip,
    Distance,
    FloatWithUncertaintiesAndUnit,
    Latitude,
    Longitude,
    SampleRate,
)

from yasmine.app.enums.xml_node import XmlNodeAttrEnum, XmlNodeEnum
from yasmine.app.exceptions.exceptions import BusinessException, ResponseEditException
from yasmine.app.handlers.equipment import EquipmentMixin
from yasmine.app.models import XmlNodeAttrValModel, XmlNodeInstModel, XmlNodeAttrModel
from yasmine.app.services.xml_service import XmlService
from yasmine.app.utils.date import parse_naive_datetime, parse_utcdatetime
from yasmine.app.utils.facade import HandlerMixin
from yasmine.app.utils.imp_exp import ConvertToInventory
from yasmine.app.utils.response_sensitivity import (
    get_updated_response_obj,
    recalculate_response_sensitivity,
)
from yasmine.app.utils.response_schema import validate_response_tree
from yasmine.app.utils.response_tree import response_tree_to_xml
from yasmine.app.utils.stationxml_codec import (
    MEASURED_ATTRIBUTE_NAMES,
    merge_measured_value,
)


UNSET = object()


class AttributeService(HandlerMixin, EquipmentMixin):
    UNSET = UNSET

    def create_attribute(
            self, attribute_id, node_id, value, spread_to_channels,
            value_meta=UNSET):
        node_inst = self.db.get(XmlNodeInstModel, node_id)
        attr = self.db.get(XmlNodeAttrModel, attribute_id)
        if node_inst is None or attr is None:
            raise BusinessException('Node or attribute not found')
        existing = self.db.query(XmlNodeAttrValModel).filter(
            XmlNodeAttrValModel.node_inst_id == node_inst.id,
            XmlNodeAttrValModel.attr_id == attr.id,
        ).first()
        if existing is not None:
            raise BusinessException(
                'StationXML allows only one "%s" value on this node' % attr.name
            )

        attr_model = XmlNodeAttrValModel()
        attr_model.node_inst = node_inst
        attr_model.attr = attr

        self._update_attribute_value(attr_model, value)
        self._update_attribute_metadata(attr_model, value_meta)
        self._update_node_shortcuts(attr_model, value)

        if spread_to_channels:
            self._spread_value_to_channels(attr_model)

        XmlService(self).update_timestamp(attr_model.node_inst.xml_id)

        return attr_model

    def update_attribute(
            self, attr_model, value, spread_to_channels, value_meta=UNSET):
        self._update_attribute_value(attr_model, value)
        self._update_attribute_metadata(attr_model, value_meta)
        self._update_node_shortcuts(attr_model, value)

        if spread_to_channels:
            self._spread_value_to_channels(attr_model)

        XmlService(self).update_timestamp(attr_model.node_inst.xml_id)

    def delete_attribute(self, db_id):
        attr_model = self.db.get(XmlNodeAttrValModel, db_id)
        if attr_model is None or attr_model.node_inst is None:
            raise BusinessException('Attribute not found')
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
        elif obj.attr.name == XmlNodeAttrEnum.DATA_AVAILABILITY:
            self._update_data_availability(obj, value)
        elif self._is_measured_attribute(obj):
            existing = obj.value_obj if obj.value is not None else None
            obj.value_obj = merge_measured_value(
                existing,
                value,
                self._measured_value_class(obj.attr.name),
            )
        elif obj.attr.name == XmlNodeAttrEnum.RESPONSE and isinstance(value, str):
            raise ResponseEditException(
                'The response was sent as text and was not saved. Select the response again.'
            )
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
        issues = validate_response_tree(value['response'])
        errors = [issue for issue in issues if issue['severity'] == 'error']
        if errors:
            message = '; '.join(
                '%s: %s' % (issue['path'], issue['message'])
                for issue in errors
            )
            raise ResponseEditException(ValueError(message))

        station_xml = ConvertToInventory(None, self).get_station_xml_for_channel(node_id)
        response_xml = response_tree_to_xml(value['response'])
        try:
            response = get_updated_response_obj(response_xml, station_xml)
            obj.value_obj = response
        except Exception as err:
            raise ResponseEditException(err)

    def _update_new_response(self, obj, value):
        recalculate = bool(value.get('recalculateSensitivity'))
        library_type = value['libraryType']
        if library_type == 'nrlv2_online':
            instconfig = value.get('instconfig')
            if not instconfig:
                raise ResponseEditException(Exception('instconfig required for NRLv2 online'))
            source = value.get('source')
            equipment = self.manage_equipment(
                obj.node_inst, instconfig, None, library_type, obj, nrlv2_source=source
            )
        else:
            sensor_keys = value.get('sensorKeys') or []
            datalogger_keys = value.get('dataloggerKeys') or []
            equipment = self.manage_equipment(
                obj.node_inst, sensor_keys, datalogger_keys, library_type, obj,
                nrl_response_type=value.get('nrlResponseType'),
            )
        for attr in equipment:
            if attr is not None:
                self.db.add(attr)
        if recalculate:
            self._recalculate_equipment_response(equipment)

    def _prepare_response_json_as_xml(self, json_obj, parent_node=None):
        if parent_node is not None:
            raise ValueError('Partial response serialization is no longer supported')
        self.response_xml_str = response_tree_to_xml(json_obj)
        return self.response_xml_str

    @staticmethod
    def _recalculate_equipment_response(equipment):
        if not equipment:
            return
        response_attr = equipment[-1]
        if response_attr is None or response_attr.value_obj is None:
            return
        response, _ = recalculate_response_sensitivity(
            response_attr.value_obj, allow_zero_gain_reset=True
        )
        response_attr.value_obj = response

    def _update_datalogger_or_sensor_attribute(self, obj, equipment):
        self._update_equipment_calibration_date([equipment])
        obj.value_obj = equipment

    def _update_equipment_attribute(self, obj, equipments):
        self._update_equipment_calibration_date(equipments)
        obj.value_obj = equipments

    @staticmethod
    def _update_data_availability(obj, value):
        if value is None or isinstance(value, DataAvailability):
            obj.value_obj = value
            return
        # Editor may send {extent:{start,end}, spans:[{numberSegments,...}]}
        # while ObsPy / older clients use top-level start/end and snake_case.
        extent = value.get('extent') if isinstance(value.get('extent'), dict) else {}
        start = value.get('start')
        end = value.get('end')
        if start is None and extent:
            start = extent.get('start')
        if end is None and extent:
            end = extent.get('end')
        spans = []
        for span in value.get('spans', []) or []:
            if isinstance(span, DataAvailabilitySpan):
                spans.append(span)
            else:
                spans.append(DataAvailabilitySpan(
                    start=span.get('start'),
                    end=span.get('end'),
                    number_of_segments=(
                        span.get('number_of_segments')
                        if span.get('number_of_segments') is not None
                        else span.get('numberSegments')
                    ),
                    maximum_time_tear=(
                        span.get('maximum_time_tear')
                        if span.get('maximum_time_tear') is not None
                        else span.get('maximumTimeTear')
                    ),
                ))
        obj.value_obj = DataAvailability(
            start=start,
            end=end,
            spans=spans,
        )

    @staticmethod
    def _measured_value_class(attribute_name):
        return {
            XmlNodeAttrEnum.LATITUDE: Latitude,
            XmlNodeAttrEnum.LONGITUDE: Longitude,
            XmlNodeAttrEnum.ELEVATION: Distance,
            XmlNodeAttrEnum.DEPTH: Distance,
            XmlNodeAttrEnum.AZIMUTH: Azimuth,
            XmlNodeAttrEnum.DIP: Dip,
            XmlNodeAttrEnum.WATER_LEVEL: FloatWithUncertaintiesAndUnit,
            XmlNodeAttrEnum.SAMPLE_RATE: SampleRate,
            XmlNodeAttrEnum.CLOCK_DRIFT_IN_SECONDS_PER_SAMPLE: ClockDrift,
        }.get(attribute_name)

    def _update_attribute_metadata(self, obj, value_meta):
        if (
            value_meta is UNSET
            or not self._is_measured_attribute(obj)
            or obj.value is None
        ):
            return
        existing = obj.value_obj
        metadata = dict(value_meta or {})
        metadata['value'] = float(existing)
        obj.value_obj = merge_measured_value(
            existing,
            metadata,
            self._measured_value_class(obj.attr.name),
        )

    @staticmethod
    def _update_equipment_calibration_date(equipments):
        for equipment in equipments:
            calibration_dates = []
            for calibration_date in equipment.calibration_dates:
                calibration_dates.append(parse_utcdatetime(calibration_date))
            equipment.calibration_dates = calibration_dates

    @staticmethod
    def _update_date_attribute(obj, value):
        obj.value_obj = parse_utcdatetime(value)

    @staticmethod
    def _update_node_shortcuts(obj, value):
        if obj.attr.name in [XmlNodeAttrEnum.CODE]:
            obj.node_inst.code = value
        elif obj.attr.name in [XmlNodeAttrEnum.START_DATE, XmlNodeAttrEnum.END_DATE]:
            py_date = None
            if isinstance(value, str):
                py_date = parse_naive_datetime(value)
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
    def _is_measured_attribute(obj):
        return obj.attr.name in MEASURED_ATTRIBUTE_NAMES

    @staticmethod
    def _is_datalogger_or_sensor_attribute(obj):
        return obj.attr.name in [XmlNodeAttrEnum.DATA_LOGGER, XmlNodeAttrEnum.SENSOR]

    @staticmethod
    def _is_edit_response_attribute(obj, value):
        return (
            obj.attr.name in [XmlNodeAttrEnum.RESPONSE]
            and isinstance(value, dict)
            and 'response' in value
        )

    @staticmethod
    def _is_new_response_attribute(obj, value):
        return (
            obj.attr.name in [XmlNodeAttrEnum.RESPONSE]
            and isinstance(value, dict)
            and 'libraryType' in value
        )

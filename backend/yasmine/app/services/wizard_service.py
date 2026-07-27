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
#
# ****************************************************************************/
from obspy import UTCDateTime
from obspy.core.inventory import Site
from sqlalchemy.orm import joinedload

from yasmine.app.handlers.equipment import EquipmentMixin
from yasmine.app.models import XmlNodeInstModel, XmlNodeModel, XmlNodeAttrModel, XmlNodeAttrValModel
from yasmine.app.services.xml_service import XmlService
from yasmine.app.utils.db import db_transaction
from yasmine.app.utils.facade import HandlerMixin
from yasmine.app.enums.xml_node import XmlNodeEnum, XmlNodeAttrEnum
from yasmine.app.utils.response_sensitivity import response_tree_to_obj, validate_response_sacpz


def _to_datetime(val):
    """Convert string/None to Python datetime for SQLite DateTime columns."""
    if val is None or val == '':
        return None
    utc = UTCDateTime(val)
    return utc.datetime


class WizardService(HandlerMixin, EquipmentMixin):
    def create_network(self, xml_id, code, start_date, end_date):
        inst = XmlNodeInstModel(
            node=self.db.get(XmlNodeModel, XmlNodeEnum.NETWORK),
            xml_id=xml_id,
            code=code,
            start_date=_to_datetime(start_date),
            end_date=_to_datetime(end_date)
        )
        self._create_attr(inst, XmlNodeAttrEnum.CODE, code)
        self._create_attr(inst, XmlNodeAttrEnum.START_DATE, start_date)
        self._create_attr(inst, XmlNodeAttrEnum.END_DATE, end_date)
        self._save_instances([inst], xml_id)
        return inst.id

    def create_station(self, xml_id, code, start_date, end_date, network_id, latitude, longitude, elevation):
        inst = XmlNodeInstModel(
            parent=self.db.get(XmlNodeInstModel, network_id),
            node=self.db.get(XmlNodeModel, XmlNodeEnum.STATION),
            xml_id=xml_id,
            code=code,
            start_date=_to_datetime(start_date),
            end_date=_to_datetime(end_date)
        )
        self._create_attr(inst, XmlNodeAttrEnum.CODE, code)
        self._create_attr(inst, XmlNodeAttrEnum.START_DATE, start_date)
        self._create_attr(inst, XmlNodeAttrEnum.END_DATE, end_date)
        self._create_attr(inst, XmlNodeAttrEnum.SITE, Site(''), False)
        self._create_attr(inst, XmlNodeAttrEnum.LATITUDE, latitude)
        self._create_attr(inst, XmlNodeAttrEnum.LONGITUDE, longitude)
        self._create_attr(inst, XmlNodeAttrEnum.ELEVATION, elevation)
        self._save_instances([inst], xml_id)
        return inst.id

    def create_channels(self, xml_id, code_list, start_date, end_date, station_id, dip_list, azimuth_list, latitude,
                        longitude, elevation, location_code, depth, library_type, sensor_keys, datalogger_keys,
                        response_tree=None):
        channel_node = self.db.get(XmlNodeModel, XmlNodeEnum.CHANNEL)
        station = self.db.get(XmlNodeInstModel, station_id)
        channels = []
        # Avoid autoflush while assembling unsaved channel instances linked to station.
        with self.db.no_autoflush:
            for i in range(len(code_list)):
                if len(code_list[i]) > 0:
                    inst = XmlNodeInstModel(
                        parent=station,
                        node=channel_node,
                        xml_id=xml_id,
                        code=code_list[i],
                        start_date=_to_datetime(start_date),
                        end_date=_to_datetime(end_date)
                    )
                    self._create_attr(inst, XmlNodeAttrEnum.CODE, code_list[i])
                    self._create_attr(inst, XmlNodeAttrEnum.START_DATE, start_date)
                    self._create_attr(inst, XmlNodeAttrEnum.END_DATE, end_date)
                    self._create_attr(inst, XmlNodeAttrEnum.LOCATION_CODE, location_code, False)
                    self._create_attr(inst, XmlNodeAttrEnum.LATITUDE, latitude)
                    self._create_attr(inst, XmlNodeAttrEnum.LONGITUDE, longitude)
                    self._create_attr(inst, XmlNodeAttrEnum.ELEVATION, elevation)
                    self._create_attr(inst, XmlNodeAttrEnum.DEPTH, depth)
                    self._create_attr(inst, XmlNodeAttrEnum.AZIMUTH, azimuth_list[i])
                    self._create_attr(inst, XmlNodeAttrEnum.DIP, dip_list[i])

                    equipment = self.manage_equipment(inst, sensor_keys, datalogger_keys, library_type)
                    if response_tree:
                        response_attr = equipment[3]
                        if response_attr is not None:
                            response_obj = response_tree_to_obj(response_tree)
                            if not response_obj.instrument_polynomial:
                                validate_response_sacpz(response_obj)
                            response_attr.value_obj = response_obj
                    for attr in equipment:
                        if attr is not None:
                            inst.attr_vals.append(attr)
                    channels.append(inst)

        self._save_instances(channels, xml_id)
        return list(map(lambda x: x.id, channels))

    def get_channel_info(self, station_node_id):
        try:
            station_node_id = int(station_node_id) if station_node_id not in (None, '') else 0
        except (TypeError, ValueError):
            station_node_id = 0
        parents_attr_vals = self.db.query(XmlNodeAttrValModel) \
            .join(XmlNodeAttrValModel.attr) \
            .options(joinedload(XmlNodeAttrValModel.attr)) \
            .filter(XmlNodeAttrValModel.node_inst_id == station_node_id) \
            .filter(XmlNodeAttrModel.name.in_([XmlNodeAttrEnum.LATITUDE,
                                               XmlNodeAttrEnum.LONGITUDE,
                                               XmlNodeAttrEnum.ELEVATION])) \
            .all()

        attr_by_name = {}
        for attr_val in parents_attr_vals:
            attr_by_name[attr_val.attr.name] = attr_val.value_obj

        def _num(val):
            if val is None or val == '':
                return 0
            try:
                return float(val)
            except (TypeError, ValueError):
                return 0

        data = {
            'id': station_node_id,
            XmlNodeAttrEnum.LATITUDE: _num(attr_by_name.get(XmlNodeAttrEnum.LATITUDE)),
            XmlNodeAttrEnum.LONGITUDE: _num(attr_by_name.get(XmlNodeAttrEnum.LONGITUDE)),
            XmlNodeAttrEnum.ELEVATION: _num(attr_by_name.get(XmlNodeAttrEnum.ELEVATION)),
            XmlNodeAttrEnum.START_DATE: '',
            XmlNodeAttrEnum.DEPTH: 0,
            '%s1' % XmlNodeAttrEnum.CODE: '',
            '%s2' % XmlNodeAttrEnum.CODE: '',
            '%s3' % XmlNodeAttrEnum.CODE: '',
            '%s1' % XmlNodeAttrEnum.DIP: 0,
            '%s2' % XmlNodeAttrEnum.DIP: 0,
            '%s3' % XmlNodeAttrEnum.DIP: 0,
            '%s1' % XmlNodeAttrEnum.AZIMUTH: 0,
            '%s2' % XmlNodeAttrEnum.AZIMUTH: 0,
            '%s3' % XmlNodeAttrEnum.AZIMUTH: 0
        }
        return data

    def _save_instances(self, inst_list, xml_id):
        with db_transaction(self.db):
            for inst in inst_list:
                self.db.add(inst)
            XmlService(self).update_timestamp(xml_id)

    def _create_attr(self, node_inst, attr_name, value, check_empty=True):
        if check_empty and (value is None or len(str(value)) == 0):
            return

        if attr_name in [XmlNodeAttrEnum.START_DATE,
                         XmlNodeAttrEnum.END_DATE,
                         XmlNodeAttrEnum.CREATION_DATE,
                         XmlNodeAttrEnum.TERMINATION_DATE]:
            value = UTCDateTime(value)

        attr = self.db.query(XmlNodeAttrModel).filter(XmlNodeAttrModel.name == attr_name).first()
        node_inst.attr_vals.append(XmlNodeAttrValModel(attr=attr, value_obj=value))

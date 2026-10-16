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


from yasmine.app.enums.library import LibraryTypeEnum
from yasmine.app.exceptions.exceptions import BusinessException
from yasmine.app.enums.xml_node import XmlNodeAttrEnum
from yasmine.app.helpers.library_helper_factory import LibraryHelperFactory
from yasmine.app.helpers.nrl.nrlv2_online import nrlv2_equipment_flags
from yasmine.app.models.inventory import XmlNodeAttrModel, XmlNodeAttrValModel


class EquipmentMixin(object):

    def recreate_attr(self, node_inst, attr_name):
        with self.db.no_autoflush:
            attr_model = self.db.query(XmlNodeAttrModel).filter(
                XmlNodeAttrModel.name == attr_name
            ).first()
            if attr_model is None:
                raise ValueError('Unknown attribute: %s' % attr_name)
            if node_inst.id:
                self.db.query(XmlNodeAttrValModel) \
                    .filter(XmlNodeAttrValModel.attr_id == attr_model.id) \
                    .filter(XmlNodeAttrValModel.node_inst_id == node_inst.id) \
                    .delete(synchronize_session=False)
        return XmlNodeAttrValModel(
            node_inst_id=node_inst.id,
            attr_id=attr_model.id,
            attr=attr_model,
        )

    def manage_equipment(self, node_inst, sensor_keys, datalogger_keys, library_type, response_attr=None, nrlv2_source=None, nrl_response_type=None):
        # The channel wizard sends libraryType "none" for "I don't need a response".
        if library_type in (None, '', 'none'):
            return None, None, None, None

        if library_type == LibraryTypeEnum.NRLV2_ONLINE:
            config = getattr(self, 'config', None)
            if config is not None and not config.get('nrlv2', 'nrlv2_online_enabled'):
                raise BusinessException('NRL Online is disabled')
            if isinstance(sensor_keys, (list, tuple)):
                parts = [str(item) for item in sensor_keys if item]
                if len(parts) != 1:
                    raise BusinessException('NRL Online needs one instrument configuration')
                instconfig = parts[0]
            else:
                instconfig = sensor_keys
            return self.manage_equipment_nrlv2(node_inst, instconfig, response_attr, source=nrlv2_source)

        if library_type == LibraryTypeEnum.NRL and nrl_response_type in ('integrated', 'soh'):
            helper = LibraryHelperFactory().get_helper(library_type)
            return self.manage_equipment_nrl_element(
                node_inst, helper, nrl_response_type, sensor_keys, response_attr
            )

        helper = LibraryHelperFactory().get_helper(library_type)

        with self.db.no_autoflush:
            sensor_attr = None
            if sensor_keys and len(sensor_keys) > 0:
                sensor_attr = self.recreate_attr(node_inst, XmlNodeAttrEnum.SENSOR)
                sensor_attr.value_obj = helper.get_sensor_equipment(sensor_keys)

            datalogger_attr = None
            if datalogger_keys and len(datalogger_keys) > 0:
                datalogger_attr = self.recreate_attr(node_inst, XmlNodeAttrEnum.DATA_LOGGER)
                datalogger_attr.value_obj = helper.get_datalogger_equipment(datalogger_keys)

            sample_rate_attr = None
            if sensor_keys and len(sensor_keys) > 0 and datalogger_keys and len(datalogger_keys) > 0:
                response_attr = response_attr or self.recreate_attr(
                    node_inst, XmlNodeAttrEnum.RESPONSE
                )
                response_attr.value_obj = helper.get_channel_response_obj(
                    sensor_keys, datalogger_keys
                )
                sample_rate = self._sample_rate_from_response(response_attr.value_obj)
                if sample_rate is not None:
                    sample_rate_attr = self.recreate_attr(
                        node_inst, XmlNodeAttrEnum.SAMPLE_RATE
                    )
                    sample_rate_attr.value_obj = sample_rate

        return sensor_attr, datalogger_attr, sample_rate_attr, response_attr

    def manage_equipment_nrlv2(self, node_inst, instconfig, response_attr=None, source=None):
        """Manage equipment for NRLv2 online (instconfig-based)."""
        app = getattr(self, 'application', None)
        helper = LibraryHelperFactory().get_helper(LibraryTypeEnum.NRLV2_ONLINE, application=app)
        has_sensor, has_datalogger = nrlv2_equipment_flags(instconfig)

        with self.db.no_autoflush:
            sensor_attr = None
            if has_sensor:
                sensor_attr = self.recreate_attr(node_inst, XmlNodeAttrEnum.SENSOR)
                sensor_attr.value_obj = helper.get_sensor_equipment(instconfig)

            datalogger_attr = None
            if has_datalogger:
                datalogger_attr = self.recreate_attr(node_inst, XmlNodeAttrEnum.DATA_LOGGER)
                datalogger_attr.value_obj = helper.get_datalogger_equipment(instconfig)

            response_attr = response_attr or self.recreate_attr(
                node_inst, XmlNodeAttrEnum.RESPONSE
            )
            response_attr.value_obj = helper.get_channel_response_obj(
                instconfig, source=source
            )

            sample_rate_attr = None
            sample_rate = self._sample_rate_from_response(response_attr.value_obj)
            if sample_rate is not None:
                sample_rate_attr = self.recreate_attr(
                    node_inst, XmlNodeAttrEnum.SAMPLE_RATE
                )
                sample_rate_attr.value_obj = sample_rate

        return sensor_attr, datalogger_attr, sample_rate_attr, response_attr

    def manage_equipment_nrl_element(self, node_inst, helper, element, keys, response_attr=None):
        """One RESP file from the offline integrated or SOH catalog."""
        with self.db.no_autoflush:
            sensor_attr = None
            datalogger_attr = None
            if element == 'integrated':
                sensor_attr = self.recreate_attr(node_inst, XmlNodeAttrEnum.SENSOR)
                sensor_attr.value_obj = helper.get_element_equipment(element, keys)
                datalogger_attr = self.recreate_attr(node_inst, XmlNodeAttrEnum.DATA_LOGGER)
                datalogger_attr.value_obj = helper.get_element_equipment(element, keys)
            elif element == 'soh':
                datalogger_attr = self.recreate_attr(node_inst, XmlNodeAttrEnum.DATA_LOGGER)
                datalogger_attr.value_obj = helper.get_element_equipment(element, keys)

            response_attr = response_attr or self.recreate_attr(
                node_inst, XmlNodeAttrEnum.RESPONSE
            )
            response_attr.value_obj = helper.get_element_response_obj(element, keys)

            sample_rate_attr = None
            sample_rate = self._sample_rate_from_response(response_attr.value_obj)
            if sample_rate is not None:
                sample_rate_attr = self.recreate_attr(
                    node_inst, XmlNodeAttrEnum.SAMPLE_RATE
                )
                sample_rate_attr.value_obj = sample_rate

        return sensor_attr, datalogger_attr, sample_rate_attr, response_attr

    @staticmethod
    def _sample_rate_from_response(response):
        """Derive output sample rate from last stage; None if missing/unsafe."""
        if not response or not getattr(response, 'response_stages', None):
            return None
        last = response.response_stages[-1]
        factor = getattr(last, 'decimation_factor', None)
        input_rate = getattr(last, 'decimation_input_sample_rate', None)
        if factor in (None, 0) or input_rate is None:
            return None
        return input_rate / factor

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


from yasmine.app.enums.xml_node import XmlNodeAttrEnum
from yasmine.app.helpers.library_helper_factory import LibraryHelperFactory
from yasmine.app.models.inventory import XmlNodeAttrModel, XmlNodeAttrValModel


class EquipmentMixin(object):

    def recreate_attr(self, node_inst, attr_name):
        attr_id = self.db.query(XmlNodeAttrModel).filter(XmlNodeAttrModel.name == attr_name).first().id
        if node_inst.id:
            self.db.query(XmlNodeAttrValModel) \
                .filter(XmlNodeAttrValModel.attr_id == attr_id) \
                .filter(XmlNodeAttrValModel.node_inst_id == node_inst.id) \
                .delete()
        return XmlNodeAttrValModel(node_inst=node_inst, attr_id=attr_id)

    def manage_equipment(self, node_inst, sensor_keys, datalogger_keys, library_type, response_attr=None):
        helper = LibraryHelperFactory().get_helper(library_type)

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
            response_attr = response_attr or self.recreate_attr(node_inst, XmlNodeAttrEnum.RESPONSE)
            response_attr.value_obj = helper.get_channel_response_obj(sensor_keys, datalogger_keys)
            decimation_input_sample_rate = response_attr.value_obj.response_stages[-1].decimation_input_sample_rate
            decimation_factor = response_attr.value_obj.response_stages[-1].decimation_factor
            sample_rate_attr = self.recreate_attr(node_inst, XmlNodeAttrEnum.SAMPLE_RATE)
            sample_rate_attr.value_obj = decimation_input_sample_rate / decimation_factor

        return sensor_attr, datalogger_attr, sample_rate_attr, response_attr

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

import unittest

import xmlunittest
from sqlalchemy.orm import joinedload

from yasmine.app.enums.xml_node import XmlNodeEnum, XmlNodeAttrEnum
from yasmine.app.models import XmlModel, XmlNodeInstModel, XmlNodeAttrValModel, UserLibraryModel, XmlNodeAttrModel
from yasmine.app.services.node_service import NodeService
from yasmine.app.tests.integration.utils.integration_util import migrate_db, remove_db, get_file_path
from yasmine.app.utils.facade import ProcessMixin
from yasmine.app.utils.imp_exp import ImportStationXml


class DefaultChannelCreationTest(unittest.TestCase, ProcessMixin, xmlunittest.XmlTestMixin):

    def __init__(self, *args, **kwargs):
        super(DefaultChannelCreationTest, self).__init__(*args, **kwargs)
        migrate_db(__class__.__name__)
        ProcessMixin.__init__(self, *args, **kwargs)

    def test_creation_channel_default_for_xml(self):
        xml = self._import_xml('stationxmls/xx_v_1_1.xml')
        station = self.db.query(XmlNodeInstModel).filter(XmlNodeInstModel.node_id == XmlNodeEnum.STATION).first()

        station_attrs = self.db.query(XmlNodeAttrValModel).filter(XmlNodeAttrValModel.node_inst_id == station.id).all()
        station_latitude = self._find_attribute_value(station_attrs, XmlNodeAttrEnum.LATITUDE)
        station_longitude = self._find_attribute_value(station_attrs, XmlNodeAttrEnum.LONGITUDE)
        station_elevation = self._find_attribute_value(station_attrs, XmlNodeAttrEnum.ELEVATION)
        station_code = self._find_attribute_value(station_attrs, XmlNodeAttrEnum.CODE)

        node_service = NodeService(self)
        channel_id = node_service.create_default_node_for_xml(xml.id, XmlNodeEnum.CHANNEL, station.id)

        channel_attrs = self.db.query(XmlNodeAttrValModel).filter(XmlNodeAttrValModel.node_inst_id == channel_id).all()
        channel_latitude = self._find_attribute_value(channel_attrs, XmlNodeAttrEnum.LATITUDE)
        channel_longitude = self._find_attribute_value(channel_attrs, XmlNodeAttrEnum.LONGITUDE)
        channel_elevation = self._find_attribute_value(channel_attrs, XmlNodeAttrEnum.ELEVATION)
        channel_code = self._find_attribute_value(channel_attrs, XmlNodeAttrEnum.CODE)

        self.assertEqual(channel_latitude, station_latitude)
        self.assertEqual(channel_longitude, station_longitude)
        self.assertEqual(channel_elevation, station_elevation)
        self.assertNotEqual(channel_code, station_code)

    def test_creation_channel_default_for_library(self):
        library = UserLibraryModel(name='test_library')
        with self.db.begin():
            self.db.add(library)
        node_service = NodeService(self)
        station_id = node_service.create_default_node_for_library(library.id, XmlNodeEnum.STATION, None)

        station_latitude = 6
        station_longitude = 9
        station_elevation = 69
        self._update_attr_value(station_id, XmlNodeAttrEnum.LATITUDE, station_latitude)
        self._update_attr_value(station_id, XmlNodeAttrEnum.LONGITUDE, station_longitude)
        self._update_attr_value(station_id, XmlNodeAttrEnum.ELEVATION, station_elevation)

        channel_id = node_service.create_default_node_for_library(library.id, XmlNodeEnum.CHANNEL, station_id)
        channel_attrs = self.db.query(XmlNodeAttrValModel).filter(XmlNodeAttrValModel.node_inst_id == channel_id).all()
        channel_latitude = self._find_attribute_value(channel_attrs, XmlNodeAttrEnum.LATITUDE)
        channel_longitude = self._find_attribute_value(channel_attrs, XmlNodeAttrEnum.LONGITUDE)
        channel_elevation = self._find_attribute_value(channel_attrs, XmlNodeAttrEnum.ELEVATION)

        self.assertEqual(station_latitude, channel_latitude)
        self.assertEqual(station_longitude, channel_longitude)
        self.assertEqual(station_elevation, channel_elevation)

    def _update_attr_value(self, node_id, attr_name, value):
        with self.db.begin():
            attr_value = self.db.query(XmlNodeAttrValModel) \
                .join(XmlNodeAttrValModel.attr) \
                .options(joinedload(XmlNodeAttrValModel.attr)) \
                .filter(XmlNodeAttrValModel.node_inst_id == node_id) \
                .filter(XmlNodeAttrModel.name == attr_name) \
                .first()
            attr_value.value_obj = value

    @staticmethod
    def _find_attribute_value(attrs, attr_name):
        return [attribute.value_obj for attribute in attrs if attribute.attr_name == attr_name][0]

    def _import_xml(self, file_name):
        with open(get_file_path(file_name), 'rb') as f:
            return ImportStationXml(file_name, f, self).run()

    def tearDown(self):
        with self.db.begin():
            self.db.query(XmlModel).delete()

    @classmethod
    def tearDownClass(cls):
        remove_db(__class__.__name__)


if __name__ == "__main__":
    unittest.main()

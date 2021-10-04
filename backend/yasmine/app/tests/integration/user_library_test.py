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


import os
import unittest
from zipfile import ZipFile

from yasmine.app.enums.xml_node import XmlNodeAttrEnum, XmlNodeEnum
from yasmine.app.models import XmlNodeAttrValModel
from yasmine.app.services.user_library_service import UserLibraryService
from yasmine.app.tests.integration.utils.integration_util import migrate_db, remove_db
from yasmine.app.utils.facade import DbMixin


class ParseUserLibraryYamlTest(unittest.TestCase, DbMixin):
    def __init__(self, *args, **kwargs):
        super(ParseUserLibraryYamlTest, self).__init__(*args, **kwargs)
        migrate_db(__class__.__name__)
        DbMixin.__init__(self, *args, **kwargs)

    def test_import_user_library_from_folder(self):
        folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data/gatito/gatito-master/')
        UserLibraryService(self).import_from_folder(folder)
        self._check_common_result()
        self._check_folder_result()

    def test_import_user_library_from_zip(self):
        file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data/gatito/gatito-master.zip')
        with ZipFile(file, 'r') as zip_file:
            UserLibraryService(self).import_from_zip(zip_file)
        self._check_common_result()

    @unittest.skip
    def test_user_library_from_url(self):
        url = "https://gitlab.com/resif/gatito/-/archive/master/gatito-master.zip"
        UserLibraryService(self).import_from_url(url)

    def _check_folder_result(self):
        data = self.db.query(XmlNodeAttrValModel).filter(XmlNodeAttrValModel.node_inst_id.is_(None)).all()
        node_id = XmlNodeEnum.STATION

        items = list((filter(lambda x: x.attr_name == XmlNodeAttrEnum.OPERATORS and x.node_id == node_id, data)))
        operator = items[0].value_obj
        self.assertIsNotNone(operator.get('agency'))
        self.assertIsNotNone(operator.get('website'))
        self.assertIsNotNone(operator.get('help'))
        self.assertEqual(2, len(operator.get('contacts')))

    def _check_common_result(self):
        data = self.db.query(XmlNodeAttrValModel).filter(XmlNodeAttrValModel.node_inst_id.is_(None)).all()

        node_id = XmlNodeEnum.NETWORK
        items = list((filter(lambda x: x.attr_name == XmlNodeAttrEnum.IDENTIFIERS and x.node_id == node_id, data)))
        self.assertEqual(2, len(items))
        self.assertIsNotNone(next((x for x in items if x.value_obj.get('value') == 'doi:10.18715/GEOSCOPE.G'), None))

        node_id = XmlNodeEnum.STATION
        items = list((filter(lambda x: x.attr_name == XmlNodeAttrEnum.VAULT and x.node_id == node_id, data)))
        self.assertEqual(22, len(items))
        self.assertIsNotNone(next((x for x in items if x.value_obj.get('value') == 'Tunnel'), None))
        items = list((filter(lambda x: x.attr_name == XmlNodeAttrEnum.GEOLOGY and x.node_id == node_id, data)))
        self.assertEqual(11, len(items))
        self.assertIsNotNone(next((x for x in items if x.value_obj.get('value') == 'O (other)'), None))
        items = list((filter(lambda x: x.attr_name == XmlNodeAttrEnum.COMMENTS and x.node_id == node_id, data)))
        self.assertEqual(12, len(items))
        self.assertIsNotNone(next((x for x in items if x.value_obj.get('value') == 'Station is down'), None))

        node_id = XmlNodeEnum.CHANNEL
        items = list((filter(lambda x: x.attr_name == XmlNodeAttrEnum.COMMENTS and x.node_id == node_id, data)))
        self.assertEqual(21, len(items))
        self.assertIsNotNone(next((x for x in items if x.value_obj.get('value') == 'Channel is down'), None))

    @classmethod
    def tearDownClass(cls):
        remove_db(__class__.__name__)


if __name__ == "__main__":
    unittest.main()

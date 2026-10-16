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
# 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
#
# ****************************************************************************/


import io
import os
import unittest

try:
    import xmlunittest
except ImportError:
    xmlunittest = None

from yasmine.app.models import XmlModel
from yasmine.app.utils.db import db_transaction
from yasmine.app.utils.facade import DbMixin
from yasmine.app.tests.integration.utils.integration_util import migrate_db, remove_db, get_file_path
from yasmine.app.utils.imp_exp import ImportStationXml, ExportStationXml


_XmlMixin = xmlunittest.XmlTestMixin if xmlunittest else object


@unittest.skipUnless(xmlunittest, 'xmlunittest is not installed')
class ImportExportStationXml(unittest.TestCase, DbMixin, _XmlMixin):

    def __init__(self, *args, **kwargs):
        super(ImportExportStationXml, self).__init__(*args, **kwargs)
        migrate_db(__class__.__name__)
        DbMixin.__init__(self, *args, **kwargs)

    def test_import_v_1_0(self):
        self._test_import('stationxmls/xx_v_1_0.xml')

    def test_import_export_v_1_2(self):
        self._test_import_export('stationxmls/xx_v_1_2.xml')

    def _test_import(self, file_name):
        path = get_file_path(file_name)
        if not os.path.isfile(path):
            self.skipTest('fixture missing: %s' % path)
        with open(path, 'rb') as f:
            xml_model = ImportStationXml(file_name, io.BytesIO(f.read()), self).run()
            self.assertIsNotNone(xml_model, 'Unable to parse xml')

    def _test_import_export(self, file_name):
        path = get_file_path(file_name)
        if not os.path.isfile(path):
            self.skipTest('fixture missing: %s' % path)
        with open(path, 'rb') as f:
            content = f.read()
            xml_model = ImportStationXml(file_name, io.BytesIO(content), self).run()
            self.assertIsNotNone(xml_model, 'Unable to parse xml')
            _, generated_content = ExportStationXml(xml_model.id, self).run()
            generated = generated_content.getvalue()
            self.assertIn(b'FDSNStationXML', generated[:500])
            if len(content) < 40000:
                self.assertXmlEquivalentOutputs(content, generated)

    def tearDown(self):
        with db_transaction(self.db):
            self.db.query(XmlModel).delete()

    @classmethod
    def tearDownClass(cls):
        remove_db(__class__.__name__)


if __name__ == "__main__":
    unittest.main()

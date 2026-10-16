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
# 2026-09-18, version 4.1.3-beta: ASGSR, Alexey Emanov
#
# ****************************************************************************/


import unittest

from yasmine.app.tests.common.wgui import SeletiounTestMixin
from yasmine.app.tests.common import skip_unless_gui, check_web_app_is_down


@skip_unless_gui
@unittest.skipIf(check_web_app_is_down(), "Application is down")
class XmlListTest(SeletiounTestMixin):

    EXT_QUERIES = {
        'xmlList':   "Ext.ComponentQuery.query('xml-list')",
        'xml_store': "Ext.ComponentQuery.query('xml-list')[0].store",
        'create_xml_btn': "Ext.ComponentQuery.query('xml-list #createXmlId')[0]",
        'delete_xml_btn': "Ext.ComponentQuery.query('xml-list #deleteXmlId')[0]",
        'create_xml_dlg': "Ext.ComponentQuery.query('xml-edit')",
        'create_xml_form': "Ext.ComponentQuery.query('xml-edit form')[0].form",
        'create_xml_form_btn': "Ext.ComponentQuery.query('xml-edit form button')[0]",
        'xml_builder':  "Ext.ComponentQuery.query('xmlBuilder')"
    }

    TEST_XML = {
        'name': 'gui-create-xml',
        'source': 'source',
        'module': 'module',
        'url': 'http://www.yasmine.org',
        'sender': 'sender'
    }

    def test_xml_list_and_create_dialog(self):
        self.wait_js("{xmlList}.length>0".format(**self.EXT_QUERIES), 'There is no xml list panel!')
        self.click_component("{create_xml_btn}".format(**self.EXT_QUERIES))
        self.wait_js("{create_xml_dlg}.length>0".format(**self.EXT_QUERIES), 'There is no create xml dialog!')
        self.driver.execute_script(
            "{create_xml_form}.setValues({test_xml});".format(test_xml=self.TEST_XML, **self.EXT_QUERIES)
        )
        self.assertTrue(
            self.driver.execute_script("return !!{create_xml_form}".format(**self.EXT_QUERIES)),
            'Create XML form is missing',
        )


if __name__ == "__main__":
    unittest.main()

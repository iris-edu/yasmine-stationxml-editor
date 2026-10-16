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
class SettingsTest(SeletiounTestMixin):

    EXT_QUERIES = {
        'settings_list':   "Ext.ComponentQuery.query('settings-list')",
        'settings_form':   "Ext.ComponentQuery.query('settings-list')[0].form",
        'settings_save_btn': "Ext.ComponentQuery.query('settings-list button')[1]"
    }

    TEST_DATA = {
        "general__date_format_long": "Y-m-d H:i:s",
        "general__date_format_short": "Y-m-d H",
        "network__code": "NE1",
        "network__num_stations": '6',
        "station__code": "HH1",
        "station__num_channels": '1',
        "channel__code": "HH",
        "network__required_fields": ['code'],
        "station__required_fields": ['code', 'latitude', 'longitude', 'elevation', 'site'],
        "channel__required_fields": ['code', 'location_code', 'latitude', 'longitude', 'elevation', 'depth'],
        "general__source": "YASMINE XML builder1",
        "general__module": "YASMINE1",
        "general__uri": "http://yasmine.org1",
        "station__spread_to_channels": True,
        "general__user_library_source_url": "",
        "general__xml_view_mode": 1
    }

    def test_settings_panel_loads(self):
        self.open_page("#settings")
        self.wait_js("{settings_list}.length>0".format(**self.EXT_QUERIES), 'There is no settings panel!')
        self.wait_js("!{is_masked}".format(**self.BASE_EXT_QUERIES), 'Masked!', silent=True)
        values = self.driver.execute_script("return {settings_form}.getValues();".format(**self.EXT_QUERIES))
        self.assertIsInstance(values, dict)
        self.assertIn('general__source', values)


if __name__ == "__main__":
    unittest.main()

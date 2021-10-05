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

from yasmine.app.enums.library import LibraryTypeEnum
from yasmine.app.helpers.library_helper_factory import LibraryHelperFactory


class LibraryHelperNrlTest(unittest.TestCase):
    _helper = None

    @classmethod
    def setUpClass(cls):
        cls._helper = LibraryHelperFactory().get_helper(LibraryTypeEnum.NRL)
        cls._helper.sync()

    def test_sensors_keys(self):
        sensors = self._helper.get_sensors_keys()
        guralp = next((x for x in sensors if x['key'] == 'Guralp'), None)
        self.assertIsNotNone(guralp)
        self.assertEqual(13, len(guralp['children']))

    def test_datalogger_keys(self):
        datalogger = self._helper.get_dataloggers_keys()
        guralp = next((x for x in datalogger if x['key'] == 'Guralp'), None)
        self.assertIsNotNone(guralp)
        self.assertEqual(6, len(guralp['children']))

    def test_load_sensor_response(self):
        sensor = self._helper.get_sensor_response_obj(['Streckeisen', 'STS-1', '360 seconds'])
        self.assertEqual('M/S', sensor.response_stages[0].input_units)

    def test_load_datalogger_response(self):
        sensor = self._helper.get_datalogger_response_obj(['REF TEK', 'RT 130 & 130-SMA', '1', '40'])
        self.assertEqual('M/S', sensor.response_stages[0].input_units)

    def test_load_channel_response(self):
        sensor_keys = ['Streckeisen', 'STS-2', '1500', '3 - installed 04/97 to present']
        datalogger_key = ['REF TEK', 'RT 130 & 130-SMA', '1', '100']
        response = self._helper.get_channel_response_obj(sensor_keys, datalogger_key)
        self.assertEqual('M/S', response.response_stages[0].input_units)


if __name__ == "__main__":
    unittest.main()

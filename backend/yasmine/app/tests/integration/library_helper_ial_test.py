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


class LibraryHelperIalTest(unittest.TestCase):
    _helper = None

    @classmethod
    def setUpClass(cls):
        cls._helper = LibraryHelperFactory().get_helper(LibraryTypeEnum.AROL)
        cls._helper.sync()

    def test_sensors_keys(self):
        sensor = self._helper.get_sensors_keys()
        self.assertEqual(10, len(sensor.get('filters')))
        self.assertEqual(48, len(sensor.get('responses')))

    def test_datalogger_keys(self):
        datalogger = self._helper.get_dataloggers_keys()
        self.assertEqual(8, len(datalogger.get('filters')))
        self.assertEqual(75, len(datalogger.get('responses')))

    def test_load_sensor_response(self):
        sensor = self._helper.get_sensor_response_obj(['streckeisen/STS1_360.response.json'])
        self.assertEqual(1, len(sensor))
        self.assertEqual(1, len(sensor[0]['response']['stages']))

    def test_load_datalogger_response(self):
        datalogger = self._helper.get_datalogger_response_obj(['reftek/RT130-G-1.response.json', 'reftek/RT130.40.response.json'])
        self.assertEqual(2, len(datalogger))
        self.assertEqual(1, len(datalogger[0]['response']['stages']))
        self.assertEqual(9, len(datalogger[1]['response']['stages']))

    def test_build_channel_response_div_by_zero(self):
        # sensor_keys = ['streckeisen/STS1_360.response.yaml']
        # datalogger_key = ['nanometrics/CENTAUR-DC.100.response.yaml', 'nanometrics/CENTAUR-G-2.response.yaml']
        # self._helper.get_channel_response_obj(sensor_keys, datalogger_key)
        pass

    def test_load_channel_response(self):
        sensor_keys = ['streckeisen/STS2-III.response.json']
        datalogger_key = ['reftek/RT130-G-1.response.json', 'reftek/RT130.40.response.json']
        response = self._helper.get_channel_response_obj(sensor_keys, datalogger_key)
        self.assertEqual('M/S', response.response_stages[0].input_units.upper())

    def test_guess_channel_code(self):
        sensor_keys = ['streckeisen/STS1_360.response.json']
        datalogger_key = ['reftek/RT130-G-1.response.json', 'reftek/RT130.40.response.json']
        code1, code2 = self._helper.guess_channel_code(sensor_keys, datalogger_key)
        self.assertEqual('', code1)
        self.assertEqual('', code2)


if __name__ == "__main__":
    unittest.main()

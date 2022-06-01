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


class NrlGuessTest(unittest.TestCase):
    _helper = None

    @classmethod
    def setUpClass(cls):
        cls._helper = LibraryHelperFactory().get_helper(LibraryTypeEnum.NRL)
        cls._helper.sync()

    def test_1(self):
        '''
            Combine Hyperion infrasound mic with Kinemetrics Rock sampled at high rate (250 sps)
        '''
        sensor_keys = ['Hyperion', 'IFS-4000']
        datalog_keys = ['Kinemetrics', 'Rock Family (Basalt, Granite, Dolomite, Obsidian)', '16', '10', 'Non-causal',
                        '250']

        chan_code, band_char = self._helper.guess_channel_code(sensor_keys, datalog_keys)
        self.assertEqual(chan_code[0], band_char, 'Channel code and band code are not equal.')

    def test_2(self):
        '''
            Combine Geo_Space/OYO low-gain short-period with Kinemetrics Rock sampled at high rate (250 sps)
        '''
        sensor_keys = ['Geo Space/OYO', 'OMNI-2400', 'none']
        datalog_keys = ['Kinemetrics', 'Rock Family (Basalt, Granite, Dolomite, Obsidian)', '16', '10', 'Non-causal',
                        '250']

        chan_code, band_char = self._helper.guess_channel_code(sensor_keys, datalog_keys)
        self.assertEqual(chan_code[0], band_char, 'Channel code and band code are not equal.')

    def test_3(self):
        '''
            Combine STS-1 broadband with Quanterra Q330HRS sampled at .01, ...., 100 sps
        '''
        sensor_keys = ['Streckeisen', 'STS-1', '360 seconds']
        datalog_keys = ['Quanterra', 'Q330HRS', '1', '0.01', 'LINEAR AT ALL SPS', 'VLP389/ULP379']
        chan_code, band_char = self._helper.guess_channel_code(sensor_keys, datalog_keys)
        self.assertEqual(chan_code[0], band_char, 'Channel code and band code are not equal.')

        datalog_keys = ['Quanterra', 'Q330HRS', '1', '1', 'LINEAR AT ALL SPS']
        chan_code, band_char = self._helper.guess_channel_code(sensor_keys, datalog_keys)
        self.assertEqual(chan_code[0], band_char, 'Channel code and band code are not equal.')

        datalog_keys = ['Quanterra', 'Q330HRS', '1', '20', 'LINEAR AT ALL SPS']
        chan_code, band_char = self._helper.guess_channel_code(sensor_keys, datalog_keys)
        self.assertEqual(chan_code[0], band_char, 'Channel code and band code are not equal.')

        datalog_keys = ['Quanterra', 'Q330HRS', '1', '100', 'LINEAR AT ALL SPS']
        chan_code, band_char = self._helper.guess_channel_code(sensor_keys, datalog_keys)
        self.assertEqual(chan_code[0], band_char, 'Channel code and band code are not equal.')

    def test_4(self):
        '''
            Channel naming wizard returns empty channel code
        '''
        sensor_keys = ['Chaparral Physics', '50A', 'High: 2 V/Pa']
        datalog_keys = ['REF TEK', 'RT 130 & 130-SMA', '1', '40']

        chan_code, band_char = self._helper.guess_channel_code(sensor_keys, datalog_keys)
        self.assertEqual(chan_code[0], band_char, 'Channel code and band code are not equal.')

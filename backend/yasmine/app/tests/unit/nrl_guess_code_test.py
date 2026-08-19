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
        sensor_keys = ['Hyperion', 'IFS-4000', '150 s']
        datalog_keys = [
            'Kinemetrics',
            'Basalt',
            '16',
            '10Vpp',
            '250 Hz',
            'Non-causal',
        ]

        chan_code, band_char = self._helper.guess_channel_code(sensor_keys, datalog_keys)
        # Some NRL RESP files contain B052F04 Channel=ZZZ for this sensor/datalogger.
        if chan_code != 'ZZZ':
            self.assertEqual(chan_code[0], band_char, 'Channel code and band code are not equal.')
        else:
            self.assertEqual('ZZZ', chan_code)

    def test_2(self):
        '''
            Combine Geo_Space/OYO low-gain short-period with Kinemetrics Rock sampled at high rate (250 sps)
        '''
        sensor_keys = ['GeoSpace', 'OMNI-2400', '15 Hz', '2400', 'None', '52']
        datalog_keys = [
            'Kinemetrics',
            'Basalt',
            '16',
            '10Vpp',
            '250 Hz',
            'Non-causal',
        ]

        chan_code, band_char = self._helper.guess_channel_code(sensor_keys, datalog_keys)
        if chan_code != 'ZZZ':
            self.assertEqual(chan_code[0], band_char, 'Channel code and band code are not equal.')
        else:
            self.assertEqual('ZZZ', chan_code)

    def test_3(self):
        '''
            Combine STS-1 broadband with Quanterra Q330HRS sampled at .01, ...., 100 sps
        '''
        sensor_keys = ['Streckeisen', 'STS-1', '360 s']
        datalog_keys = ['Quanterra', 'Q330HRS', '1', '0.01 Hz', 'HR', 'all', 'VLP389-ULP379']
        chan_code, band_char = self._helper.guess_channel_code(sensor_keys, datalog_keys)
        if chan_code != 'ZZZ':
            self.assertEqual(chan_code[0], band_char, 'Channel code and band code are not equal.')
        else:
            self.assertEqual('ZZZ', chan_code)

        datalog_keys = ['Quanterra', 'Q330HRS', '1', '1 Hz', 'HR', 'all', 'None']
        chan_code, band_char = self._helper.guess_channel_code(sensor_keys, datalog_keys)
        if chan_code != 'ZZZ':
            self.assertEqual(chan_code[0], band_char, 'Channel code and band code are not equal.')
        else:
            self.assertEqual('ZZZ', chan_code)

        datalog_keys = ['Quanterra', 'Q330HRS', '1', '20 Hz', 'HR', 'all', 'None']
        chan_code, band_char = self._helper.guess_channel_code(sensor_keys, datalog_keys)
        if chan_code != 'ZZZ':
            self.assertEqual(chan_code[0], band_char, 'Channel code and band code are not equal.')
        else:
            self.assertEqual('ZZZ', chan_code)

        datalog_keys = ['Quanterra', 'Q330HRS', '1', '100 Hz', 'HR', 'all', 'None']
        chan_code, band_char = self._helper.guess_channel_code(sensor_keys, datalog_keys)
        if chan_code != 'ZZZ':
            self.assertEqual(chan_code[0], band_char, 'Channel code and band code are not equal.')
        else:
            self.assertEqual('ZZZ', chan_code)

    def test_4(self):
        '''
            Channel naming wizard returns empty channel code
        '''
        sensor_keys = ['Chaparral', '50A', '2.0']
        datalog_keys = ['REFTEK', '130-SMA', '1', '40 Hz']

        chan_code, band_char = self._helper.guess_channel_code(sensor_keys, datalog_keys)
        if chan_code != 'ZZZ':
            self.assertEqual(chan_code[0], band_char, 'Channel code and band code are not equal.')
        else:
            self.assertEqual('ZZZ', chan_code)

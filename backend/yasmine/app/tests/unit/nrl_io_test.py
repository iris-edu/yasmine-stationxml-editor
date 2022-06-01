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

from yasmine.app.enums.library import LibraryTypeEnum
from yasmine.app.helpers.library_helper_factory import LibraryHelperFactory
from yasmine.app.settings import NRL_ROOT


class NrlIoTest(unittest.TestCase):
    _helper = None

    @classmethod
    def setUpClass(cls):
        cls._helper = LibraryHelperFactory().get_helper(LibraryTypeEnum.NRL)
        cls._helper.sync()

    def test_1_sync_nrl_and_get_channel_res(self):
        self.assertTrue(len(os.listdir(NRL_ROOT)) > 0, "NRL is not synchronized")

        res = self._helper.get_channel_response_obj(
            ['Streckeisen', 'STS-1', '360 seconds'],
            ['REF TEK', 'RT 130 & 130-SMA', '1', '40'])

        self.assertIsNot(res, "No response")

    def test_2_sync_nrl_and_get_sensor_resp(self):
        self.assertTrue(len(os.listdir(NRL_ROOT)) > 0, "NRL is not synchronized")

        res = self._helper.get_sensor_response_str(['Streckeisen', 'STS-1', '360 seconds'])

        self.assertIsNotNone(res, "No response")

    def test_3_sync_nrl_and_get_datalogger_resp(self):
        self.assertTrue(len(os.listdir(NRL_ROOT)) > 0, "NRL is not synchronized")

        res = self._helper.get_datalogger_response_str(['REF TEK', 'RT 130 & 130-SMA', '1', '40'])

        self.assertIsNotNone(res, "No response")

    def test_4_sync_nrl_and_get_res(self):
        self.assertTrue(len(os.listdir(NRL_ROOT)) > 0, "NRL is not synchronized")

        res = self._helper.get_channel_response_obj(
            ['Kinemetrics', 'Episensor (ES-T, ES-U, ES-U2, DS-DH, SBEPI)', '+/- 2.5V Single-ended', '0.25g'],
            ['REF TEK', 'RT 130 & 130-SMA', '1', '100'])

        self.assertIsNotNone(res, "No response")

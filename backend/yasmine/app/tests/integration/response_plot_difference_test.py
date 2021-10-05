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
# ****************************************************************************/
import os
import unittest

from yasmine.app.enums.library import LibraryTypeEnum
from yasmine.app.helpers.library_helper_factory import LibraryHelperFactory
from yasmine.app.helpers.utils.utils import ChannelUtils
from yasmine.app.settings import MEDIA_ROOT


class ResponsePlotDifferenceTest(unittest.TestCase):
    _helper = None

    @classmethod
    def setUpClass(cls):
        # cls._helper = LibraryHelperFactory().get_helper(LibraryTypeEnum.NRL)
        cls._helper = LibraryHelperFactory().get_helper(LibraryTypeEnum.AROL)
        cls._helper.sync()

    def test_difference_plot(self):

        _use_arol = True

        if _use_arol:
            sensor1_keys = ['streckeisen/STS1_360.response.json']
            datalogger1_key = ['reftek/RT130-G-1.response.json', 'reftek/RT130.40.response.json']
            sensor2_keys = sensor1_keys
            datalogger2_key = datalogger1_key
        else:
            sensor1_keys = ['Kinemetrics', 'Episensor (ES-T, ES-U, ES-U2, DS-DH, SBEPI)', '+/- 2.5V Single-ended', '0.25g']
            # sensor1_keys = ['Streckeisen', 'STS-1', '360 seconds']
            datalogger1_key = ['REF TEK', 'RT 130 & 130-SMA', '1', '100']

            sensor2_keys = ['Kinemetrics', 'Episensor (ES-T, ES-U, ES-U2, DS-DH, SBEPI)', '+/- 2.5V Single-ended', '0.25g']
            # sensor2_keys = ['Streckeisen', 'STS-1', '360 seconds']
            datalogger2_key = ['REF TEK', 'RT 130 & 130-SMA', '1', '100']

        response1 = self._helper.get_channel_response_obj(sensor1_keys, datalogger1_key)
        response2 = self._helper.get_channel_response_obj(sensor2_keys, datalogger2_key)

        plot_folder = os.path.join(MEDIA_ROOT, 'diff_plots')
        file_name = f'response_plot_diff_test'
        ChannelUtils.create_response_plot_difference(
            response1,
            response2,
            plot_folder,
            file_name,
            0.001,
            100.)


if __name__ == "__main__":
    unittest.main()

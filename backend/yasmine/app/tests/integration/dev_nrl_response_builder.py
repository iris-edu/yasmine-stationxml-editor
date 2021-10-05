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

from obspy.core.inventory import Response
from obspy.core.inventory import Inventory, Network, Station, Channel, Site
from obspy.core.utcdatetime import UTCDateTime

from yasmine.app.enums.library import LibraryTypeEnum
from yasmine.app.helpers.library_helper_factory import LibraryHelperFactory


class ArolResponseBuilderTest(unittest.TestCase):
    _helper = None

    @classmethod
    def setUpClass(cls):
        cls._helper = LibraryHelperFactory().get_helper(LibraryTypeEnum.NRL)
        cls._helper.sync()

    def test_load_channel_response(self):
        # import matplotlib
        # matplotlib.use('TkAgg')
        sensor_keys = ['Kinemetrics', 'Episensor (ES-T, ES-U, ES-U2, DS-DH, SBEPI)', '+/- 2.5V Single-ended', '0.25g']
        sensor_keys = ['Sercel/Mark Products', 'L-22D', '325 Ohms', '1327 Ohms']
        sensor_keys = ['Sercel/Mark Products', 'L-22E', '325 Ohms', '1771 Ohms']
        sensor_keys = ['Sercel/Mark Products', 'L-22D', '5470 Ohms', '20000 Ohms']
        sensor_keys = ['Streckeisen', 'STS-2', '1500', '3 - installed 04/97 to present']
        datalogger_key = ['REF TEK', 'RT 130 & 130-SMA', '1', '100']
        # datalogger_key = ['REF TEK', 'RT 130 & 130-SMA', '1', '40']
        # datalogger_key = ['Guralp', 'CMG-6TD', '141-150', '140', '200']
        response = self._helper.get_channel_response_obj(sensor_keys, datalogger_key)
        # print(response)
        '''
        for stage in response.response_stages:
            print("Stage:%d gain:%f f:%f dec_delay:%s dec_corr:%s input_srate:%s dec_fac:%s" %
                  (stage.stage_sequence_number, stage.stage_gain, stage.stage_gain_frequency,
                   stage.decimation_delay, stage.decimation_correction, stage.decimation_input_sample_rate,
                   stage.decimation_factor))
        '''
        # stage = 10
        # print(response.response_stages[stage])
        # print(response.response_stages[stage].cf_transfer_function_type)
        # for i, coeff in enumerate(response.response_stages[stage].numerator):
        #   # print(i, coeff)

        # response.plot(min_freq=.001)
        # response.plot(min_freq=.001, end_stage=1, label='STS-2 NRL end_stage=1')
        # response.plot(min_freq=.001, label='STS-2 NRL all stages')
        # response.plot(min_freq=.00001, start_stage=3, end_stage=3, label='STS-2 NRL stage=3')

        '''
        from yasmine.app.helpers.utils.utils import ChannelUtils
        filename = 'sts2_nrl'
        csv_file = ChannelUtils.create_response_csv(response, folder='./out', file_name=filename,
                                                    min_frequency=0.001, max_frequency=None, fstep=0.1)
        resp_file = ChannelUtils.create_response_plot(response, folder='./out', file_name=filename,
                                                      min_frequency=0.001, max_frequency=None)
        # resp = ChannelUtils.get_response_csv(response, min_frequency=0.001, max_frequency=50., fstep=0.1)
        print(csv_file)
        print(resp_file)
        '''

        # self.assertEqual('M/S**2', response.response_stages[0].input_units)
        self.assertEqual('M/S', response.response_stages[0].input_units)


if __name__ == "__main__":
    unittest.main()

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
        cls._helper = LibraryHelperFactory().get_helper(LibraryTypeEnum.AROL)
        cls._helper.sync()

    def test_build_channel_response_div_by_zero(self):
        # The following combination of Datalogger and Sensor files cause a division by zero error
        # sensor_keys = ['streckeisen/STS1_360.response.yaml']
        # datalogger_key = ['nanometrics/CENTAUR-DC.100.response.yaml', 'nanometrics/CENTAUR-G-2.response.yaml']
        # self._helper.get_channel_response_obj(sensor_keys, datalogger_key)
        pass

    def test_load_channel_response(self):
        sensors = [
            ['Guralp', 'CMG3C.CG3C-LIT-T34498.E.20070314000000'],
            ['Guralp', 'CMG40T.CG40-RIS-T41000.Z.20000224000000.present'],
            ['Guralp', 'CMG5T.CG5T-RIS-0T5245.Z.200208280000000.present'],
            ['Geotech', 'GS13'],
            ['Lennartz', 'LE3D20S'],
            ['Nanometrics', 'T120QA'],
            ['Nanometrics', 'TRILLIUM_240'],
            ['Streckeisen', 'STS2-I'],
            ['Carnegie', 'SACKS-EVERTSON'],
        ]

        dataloggers = [
            ['Guralp', 'GURALP.G.DM243M-XXXX.100'],
            ['KINEMETRICS', 'KINEMETRICS.G.K2.200'],
            ['Nanometrics', 'TRIDENT.G.XXXX.100'],
            ['QUANTERRA', 'Q330.HR.XXXX.100'],
            ['REFTEK', 'R72A07.G.XXXX.40'],
            ['REFTEK', 'REFTEK.G.R130-XXXX.40'],
        ]

        separator = ' '
        if 0:
            for sensor_keys in sensors:
                print(sensor_keys)
                for datalogger_keys in dataloggers:
                    label = separator.join(sensor_keys + datalogger_keys)
                    print(label)
                    response = self._helper.get_channel_response_obj(sensor_keys, datalogger_keys)
                    nstages = len(response.response_stages)
                    if nstages > 4:
                        response.plot(0.001, output="VEL", end_stage=nstages-2, unwrap_phase=True, sampling_rate=100., label=label)
                    else:
                        response.plot(0.001, output="VEL", unwrap_phase=False, sampling_rate=100., label=label)

            exit()

        sensor_keys = sensors[3]
        sensor_keys = sensors[1]
        sensor_keys = sensors[-1]
        datalogger_keys = dataloggers[5]
        label = separator.join(sensor_keys + datalogger_keys)

        response = self._helper.get_channel_response_obj(sensor_keys, datalogger_keys)

        # print(response)
        for i, stage in enumerate(response.response_stages):
            print(stage)
        # response.plot(0.001, output="VEL")
        # MTH: This drops the final FIR decimation stage from plotting so the phase looks better:

        # MTH: response should *either* have a .instrument_sensitivity -or- .instrument_polynomial
        if response.instrument_polynomial is not None:
            print("This is a polynomial response --> Don't plot!")

        else:
            nstages = len(response.response_stages)
            # response.plot(0.001, output="VEL", end_stage=nstages-2, unwrap_phase=True, sampling_rate=100., label=label)
            if nstages > 4:
                response.plot(0.001, output="VEL", end_stage=nstages-2, unwrap_phase=True, sampling_rate=100., label=label)
            else:
                response.plot(0.001, output="VEL", unwrap_phase=False, sampling_rate=100., label=label)

        self.assertTrue(type(response) is Response)

        self.write_stationXML(response)

        return

    def test_load_channel_response(self):
        # sensor_keys = ['streckeisen/STS1_360.response.json']
        # sensor_keys = ['guralp/CMG3E.response.json']
        # sensor_keys = ['streckeisen/STS2-I.response.json']
        # sensor_keys = ['streckeisen/STS1_360.response.json']
        # sensor_keys = ['halliburton/pinnacle.14k.temp.response.json']
        # sensor_keys = ['other/Insight_temperature.json']
        # sensor_keys = ['other/YSI-44031.json']
        sensor_keys = ['streckeisen/STS2-III.response.json']

        datalogger_key = ['reftek/RT130-G-1.response.json', 'reftek/RT130.40.response.json']
        response = self._helper.get_channel_response_obj(sensor_keys, datalogger_key)

        correct_response = 0
        correct_response = 1

        if correct_response:
            delays = [0,
                      .00013672,
                      .00046875,
                      .0009375,
                      .001875,
                      .00375,
                      .0075,
                      .125,
                      .585]

            for stage in response.response_stages:
                sequence = stage.stage_sequence_number
                if sequence == 3:   # AO Digitizer
                    stage.stage_gain = 6.29129E5
                if sequence == 1:
                    stage.stage_gain_frequency = 1.0
                else:
                    stage.stage_gain_frequency = 0.05

                offset = 3
                if sequence > 2:
                    stage.decimation_delay = delays[sequence-offset]
                    stage.decimation_correction = delays[sequence-offset]

            response.recalculate_overall_sensitivity(frequency=1.0)

        '''
        for stage in response.response_stages:
            print("Stage:%d gain:%f f:%f dec_delay:%s dec_corr:%s input_srate:%s dec_fac:%s" %
                  (stage.stage_sequence_number, stage.stage_gain, stage.stage_gain_frequency,
                   stage.decimation_delay, stage.decimation_correction, stage.decimation_input_sample_rate,
                   stage.decimation_factor))

        print(response)
        for stage in response.response_stages:
            print("Stage:%d gain:%f f:%f" % (stage.stage_sequence_number, stage.stage_gain, stage.stage_gain_frequency))
        response.plot(min_freq=.001)

        # response.plot(.001, output='VEL', start_stage=1, unwrap_phase=True)
        filename = 'sts1'
        filename = 'ysi'
        filename = 'sts2_ial'
        from yasmine.app.helpers.utils.utils import ChannelUtils
        csv_file = ChannelUtils.create_response_csv(response, folder='./out', file_name=filename,
                                                    min_frequency=0.001, max_frequency=None, fstep=0.1)
        resp_file = ChannelUtils.create_response_plot(response, folder='./out', file_name=filename,
                                                      min_frequency=0.001, max_frequency=None)
        print(csv_file)
        print(resp_file)
        '''
        # from yasmine.app.utils.response_plot import plot_polynomial_resp
        # outfile = plot_polynomial_resp(response, folder='./out', outfile='polynomial_plot')

        self.assertEqual('M/S', response.response_stages[0].input_units.upper())

    @staticmethod
    def write_stationXML(response):
        # starttime = UTCDateTime("2004-10-01")
        # endtime = UTCDateTime("2004-10-02")
        inventory = Inventory(networks=[], source="isti")
        network = Network(code='BK')
        inventory.write("Test.xml", format="stationxml", validate=False)
        station = Station(code='ANMO',
                          latitude=34.945911,
                          longitude=-106.457199,
                          elevation=1820.0,
                          creation_date=UTCDateTime(1970, 1, 1),       # required
                          site=Site(name='Albuquerque, New Mexico, USA')  # required
                          )

        channel = Channel(code='LKS',
                          location_code='30',      # required
                          latitude=34.945911,      # required
                          longitude=-106.457199,   # required
                          elevation=1820.0,    # required
                          depth=0.,            # required
                          )

        channel.response = response
        station.channels = [channel]
        network.stations = [station]
        inventory.networks = [network]

        inventory.write("Test.xml", format="stationxml", validate=False)


if __name__ == "__main__":
    unittest.main()

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


import re


class NrlChannelCodeHelper:
    def __init__(self, sensors, dataloggers, *_, **__):
        self.sensors = sensors
        self.dataloggers = dataloggers

    def guess_code(self, sensors_keys, datalogger_keys, datalogger):
        sensor_code = self.read_channel_code_from_NRL(sensors_keys, self.sensors)
        datalogger_code = self.read_channel_code_from_NRL(datalogger_keys, self.dataloggers)

        sample_rate = None
        if datalogger:
            sample_rate_ptr = re.search('([0-9]*\.?[0-9]+)\s+sps', datalogger)
            if sample_rate_ptr and sample_rate_ptr[1]:
                sample_rate = float(sample_rate_ptr[1])

        chan_code = self.combine_channel_codes(sensor_code, datalogger_code)
        band_char = self.band_code(sample_rate, True if sensor_code[0] == 'S' else False)
        return chan_code, band_char

    def band_code(self, sample_rate, short_period=False):
        """
            Lookup 1-char band_code from sample_rate
            Provides a check on simply grabbing the code from the
                appropriate NRL RESP file
        """

        L = 1
        V = 0.1
        U = 0.01

        if sample_rate >= 1000:
            band_code = 'F' if not short_period else 'G'
        elif sample_rate >= 250:
            band_code = 'C' if not short_period else 'D'
        elif sample_rate >= 80:
            band_code = 'H' if not short_period else 'E'
        elif sample_rate >= 10:
            band_code = 'B' if not short_period else 'S'
        elif sample_rate > 1:
            band_code = 'M'
        elif (0.9 * L) < sample_rate < (1.1 * L):
            band_code = 'L'
        elif (0.9 * V) < sample_rate < (1.1 * V):
            band_code = 'V'
        elif (0.9 * U) < sample_rate < (1.1 * U):
            band_code = 'U'
        elif 0.0001 <= sample_rate < 0.001:
            band_code = 'R'
        elif 0.00001 <= sample_rate < 0.0001:
            band_code = 'T'
        elif sample_rate < 0.00001:
            band_code = 'Q'
        else:
            band_code = None  # Unknown
            print("Unknown sample_rate:%s" % sample_rate)

        return band_code

    def is_single_channel(self, sensor_code):
        """
        if True --> we might want to restrict the # of chans
            that can be created from this sensor to 1.
        This could be use, for example, if user requests 3 channels from
            a sensor (e.g., BDF = microphone) that we know to be only 1 channel.
        """
        # Infrasound/Microphones and Indiv.Channel Sensors (e.g., STS-1 Horizontal) are single_channel
        single_channel_sensors = ['BDF', 'BHE']
        if sensor_code in single_channel_sensors:
            return True
        else:
            return False

    def combine_channel_codes(self, sensor_code, datalogger_code):
        """
            Use input B052F04 Channel code from NRL sensor + datalogger blockettes
                to deduce combined channel code (to be created by YASMINE wizard)

            [2018-09-06]
            Here is the entire set of sensor chan codes in the NRL:
            {'BHZ', 'SLZ', 'BJZ', 'BNZ', 'BDF', 'SHZ', 'BHE'}
            And here is the set of datalogger_chan codes
            {'BHZ', 'SLZ', 'GLZ', 'LHZ', 'HHZ', 'CHZ', 'VHZ', 'LLZ', 'UHZ', 'MLZ', 'DLZ', 'SHZ', 'GHZ', 'ELZ', 'FHZ', 'DHZ', 'MHZ'}

        """
        chan_code = None

        if sensor_code[0] == 'S':  # Short-period sensor
            if datalogger_code[0] == 'H':  # High sample rate rules
                chan_code = 'E' + sensor_code[1:3]
            elif datalogger_code[0] in ['C', 'D']:
                chan_code = 'D' + sensor_code[1:3]
            elif datalogger_code[0] in ['F', 'G']:
                chan_code = 'G' + sensor_code[1:3]
            else:  # Normal sample rate (e.g., <= 80 sps)
                chan_code = sensor_code
        else:  # Everything else
            chan_code = datalogger_code[0] + sensor_code[1:3]

        return chan_code

    def read_channel_code_from_NRL(self, resp_keys, nrl_dataloggers_or_sensors):
        """
            given the NRL sensor or datalogger keys, find the RESP file and scan it for field B052F04
        """

        response = nrl_dataloggers_or_sensors

        for key in resp_keys:
            response = response[key]
        resp_file = response[1]

        chan = None
        with open(resp_file) as f:
            for line in f:
                # B052F04     Channel:     CHZ
                if line[0:7] == "B052F04":
                    chan = line.split()[2]
                    break

        return chan

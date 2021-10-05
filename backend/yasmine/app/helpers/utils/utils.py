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
import numpy as np

from yasmine.app.utils.response_plot import plot_polynomial_resp, get_polynomial_resp_csv


class ChannelUtils:

    @staticmethod
    def create_response_csv(response, folder, file_name, min_frequency=0.001, max_frequency=None, fstep=0.1):
        if response.instrument_polynomial is not None:
            return get_polynomial_resp_csv(response, folder, file_name)
        sampling_rate = None
        last_stage = response.response_stages[-1]
        if last_stage.decimation_factor != 0:
            sampling_rate = last_stage.decimation_input_sample_rate / last_stage.decimation_factor

        # If no max_frequency given, calc response up to fnyq = sampling_rate/2
        # else: shift sampling_rate so that fNyq = max_frequency
        if max_frequency:
            sampling_rate = 2 * max_frequency
        else:
            max_frequency = sampling_rate / 2.

        freqs = np.arange(min_frequency, max_frequency, fstep)

        resp = response.get_evalresp_response_for_frequencies(
            freqs,
            output="VEL",
            start_stage=1,
            end_stage=None)

        camp = np.abs(resp)
        rad2deg = 180./np.pi
        cang = np.angle(resp) * rad2deg

        os.makedirs(folder, exist_ok=True)
        sanitized_file_name = file_name.replace('/', '_').replace('\\', '_') + '.csv'
        file_path = os.path.join(folder, f'{sanitized_file_name}')

        import csv
        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Frequency", "Amplitude", "Phase [deg]"])
            for i, freq in enumerate(freqs):
                # print(i, freq, camp[i], cang[i])
                writer.writerow([freq, camp[i], cang[i]])

        return sanitized_file_name

    @staticmethod
    def create_response_plot(response, folder, file_name, min_frequency=0.001, max_frequency=None):
        import matplotlib
        matplotlib.use('Agg')

        if response.instrument_polynomial is not None:
            # MTH: this label is not propagating to plot:
            return plot_polynomial_resp(response, label='Polynomial Response', axes=None, folder=folder, outfile=file_name)
        sampling_rate = None
        last_stage = response.response_stages[-1]
        if last_stage.decimation_factor != 0:
            sampling_rate = last_stage.decimation_input_sample_rate / last_stage.decimation_factor

        if max_frequency:
            sampling_rate = 2 * max_frequency

        os.makedirs(folder, exist_ok=True)
        sanitized_file_name = file_name.replace('/', '_').replace('\\', '_') + '.png'
        file_path = os.path.join(folder, f'{sanitized_file_name}')

        # MTH: If the phase response looks funny, it's probably not a wrap issue,
        #      but an issue of missing the decimation delays/corrections for the FIR stages
        #      in the AROL lib.
        response.plot(
            min_frequency,
            output="VEL",
            start_stage=1,
            end_stage=None,
            unwrap_phase=False,
            sampling_rate=sampling_rate,
            outfile=file_path)

        return sanitized_file_name

    @staticmethod
    def create_response_plot_difference(resp1, resp2, folder, file_name, min_frequency=0.001, max_frequency=None):
        os.makedirs(folder, exist_ok=True)
        sanitized_file_name = file_name.replace('/', '_').replace('\\', '_') + '.png'
        file_path = os.path.join(folder, f'{sanitized_file_name}')

        sampling_rate = None
        last_stage = resp1.response_stages[-1]
        if last_stage.decimation_factor != 0:
            sampling_rate = last_stage.decimation_input_sample_rate / last_stage.decimation_factor

        if max_frequency:
            sampling_rate = 2 * max_frequency

        # Here should be a code which generates a plot in PNG format and stores it under $file_path

        from yasmine.app.utils.response_plot import plot_diff_resp
        import matplotlib
        matplotlib.use('Agg')

        plot_diff_resp(resp1, resp2,
                       min_frequency,
                       output="VEL",
                       start_stage=None,
                       end_stage=None,
                       unwrap_phase=False,
                       sampling_rate=sampling_rate,
                       plot_degrees=True,
                       outfile=file_path)

        return sanitized_file_name

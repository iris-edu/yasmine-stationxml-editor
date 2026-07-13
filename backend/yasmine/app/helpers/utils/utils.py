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
# NRLv2 online support (2026): ASGSR, Alexey Emanov.
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

from yasmine.app.utils.response_plot import (
    plot_polynomial_resp,
    get_polynomial_resp_csv,
    detect_plot_output,
    apply_bode_axis_labels,
    amplitude_ylabel,
    save_bode_figure,
)


def _sample_rate_from_response(response):
    """Derive sampling rate from last response stage; None if unavailable."""
    stages = getattr(response, 'response_stages', None) or []
    if not stages:
        return None
    last = stages[-1]
    factor = getattr(last, 'decimation_factor', None)
    input_rate = getattr(last, 'decimation_input_sample_rate', None)
    if factor in (None, 0) or input_rate is None:
        return None
    return input_rate / factor


class ChannelUtils:

    @staticmethod
    def create_response_csv(response, folder, file_name, min_frequency=0.001, max_frequency=None,
                            fstep=0.1, instconfig=None):
        if response.instrument_polynomial is not None:
            return get_polynomial_resp_csv(response, folder, file_name)
        sampling_rate = _sample_rate_from_response(response)
        plot_output = detect_plot_output(response, instconfig)

        # If no max_frequency given, calc response up to fnyq = sampling_rate/2
        # else: shift sampling_rate so that fNyq = max_frequency
        if max_frequency:
            sampling_rate = 2 * max_frequency
        else:
            max_frequency = (sampling_rate / 2.) if sampling_rate and sampling_rate > 0 else 100.0

        min_frequency = float(min_frequency) if min_frequency is not None else 0.001
        max_frequency = float(max_frequency) if max_frequency is not None else 100.0
        # Use log-spaced frequencies (max 250 points) to avoid huge evalresp cost
        # for FIR-heavy responses (e.g. Sercel SlimWave: 33k coefficients).
        nfreqs = 250
        freqs = np.logspace(np.log10(min_frequency), np.log10(max_frequency), nfreqs)

        resp = response.get_evalresp_response_for_frequencies(
            freqs,
            output=plot_output,
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
            writer.writerow(["Frequency [Hz]", amplitude_ylabel(plot_output, response), "Phase [deg]"])
            for i, freq in enumerate(freqs):
                # print(i, freq, camp[i], cang[i])
                writer.writerow([freq, camp[i], cang[i]])

        return sanitized_file_name

    @staticmethod
    def create_response_plot(response, folder, file_name, min_frequency=0.001, max_frequency=None,
                             instconfig=None):
        import matplotlib
        matplotlib.use('Agg')

        min_frequency = float(min_frequency) if min_frequency is not None else 0.001
        plot_output = detect_plot_output(response, instconfig)

        if response.instrument_polynomial is not None:
            # MTH: this label is not propagating to plot:
            return plot_polynomial_resp(response, label='Polynomial Response', axes=None, folder=folder, outfile=file_name)
        sampling_rate = _sample_rate_from_response(response)

        if max_frequency:
            sampling_rate = 2 * max_frequency

        # ObsPy requires sampling_rate; use 200 Hz if unknown or zero (nyquist=100 Hz)
        if sampling_rate is None or sampling_rate <= 0:
            sampling_rate = 200.0

        os.makedirs(folder, exist_ok=True)
        sanitized_file_name = file_name.replace('/', '_').replace('\\', '_') + '.png'
        file_path = os.path.join(folder, f'{sanitized_file_name}')

        # Create figure with larger size for better display in comparison mode
        import matplotlib.pyplot as plt
        fig = plt.figure(figsize=(12, 8))
        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212, sharex=ax1)
        # MTH: If the phase response looks funny, it's probably not a wrap issue,
        #      but an issue of missing the decimation delays/corrections for the FIR stages
        #      in the AROL lib.
        response.plot(
            min_frequency,
            output=plot_output,
            start_stage=1,
            end_stage=None,
            unwrap_phase=False,
            sampling_rate=sampling_rate,
            axes=[ax1, ax2],
            outfile=None)
        apply_bode_axis_labels(fig, plot_output, response, plot_degrees=False)
        save_bode_figure(fig, file_path)
        plt.close(fig)

        return sanitized_file_name

    @staticmethod
    def create_response_plot_difference(resp1, resp2, folder, file_name, min_frequency=0.001,
                                        max_frequency=None, instconfig=None):
        os.makedirs(folder, exist_ok=True)
        sanitized_file_name = file_name.replace('/', '_').replace('\\', '_') + '.png'
        file_path = os.path.join(folder, f'{sanitized_file_name}')

        sampling_rate = _sample_rate_from_response(resp1)
        plot_output = detect_plot_output(resp1, instconfig)

        if max_frequency:
            sampling_rate = 2 * max_frequency

        if sampling_rate is None or sampling_rate <= 0:
            sampling_rate = 200.0

        from yasmine.app.utils.response_plot import plot_diff_resp
        import matplotlib
        matplotlib.use('Agg')

        plot_diff_resp(resp1, resp2,
                       min_frequency,
                       output=plot_output,
                       start_stage=None,
                       end_stage=None,
                       unwrap_phase=False,
                       sampling_rate=sampling_rate,
                       plot_degrees=True,
                       outfile=file_path)

        return sanitized_file_name

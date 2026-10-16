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
# 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
#
# ****************************************************************************/


import os
import numbers

import numpy as np

from yasmine.app.utils.response_plot import (
    plot_polynomial_resp,
    get_polynomial_resp_csv,
    detect_plot_output,
    apply_bode_axis_labels,
    amplitude_ylabel,
    save_bode_figure,
    INVALID_STORED_RESPONSE,
    _is_response_object,
)


def _positive_float(value):
    """Finite number greater than zero, or None for missing and non-numeric values."""
    if isinstance(value, (str, bytes)):
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
    elif isinstance(value, numbers.Real) and not isinstance(value, bool):
        number = float(value)
    else:
        return None
    if number != number or number <= 0 or number == float('inf'):
        return None
    return number


def _sample_rate_from_response(response):
    """Derive sampling rate from last response stage; None if unavailable."""
    stages = getattr(response, 'response_stages', None) or []
    try:
        last = stages[-1]
    except (TypeError, IndexError, KeyError):
        return None
    factor = _positive_float(getattr(last, 'decimation_factor', None))
    input_rate = _positive_float(getattr(last, 'decimation_input_sample_rate', None))
    if factor is None or input_rate is None:
        return None
    return input_rate / factor


# ObsPy builds nfft = 2 * Max / Min points. Stay at or under this count.
PLOT_POINT_BUDGET = 4000000
# Below this Min, Max is reduced so the point count stays inside the budget.
PLOT_MIN_WITHOUT_MAX_REDUCTION = 0.001
# Requested Max never exceeds the response sample rate, nor this ceiling.
ABSOLUTE_MAX_HZ = 20000.0


def _stage_type_label(stage):
    """Short filter/stage type name for plot UI labels."""
    name = type(stage).__name__
    for suffix in ('TypeResponseStage', 'ResponseStage', 'Type'):
        if name.endswith(suffix) and name != suffix:
            name = name[: -len(suffix)]
            break
    return name or 'Stage'


def response_plot_stages(response):
    """List stage sequence numbers and labels for the plot stage selectors."""
    stages = getattr(response, 'response_stages', None) or []
    result = []
    for stage in stages:
        number = getattr(stage, 'stage_sequence_number', None)
        if number is None:
            continue
        try:
            number = int(number)
        except (TypeError, ValueError):
            continue
        result.append({
            'number': number,
            'label': 'Stage %d: %s' % (number, _stage_type_label(stage)),
        })
    return result


def parse_plot_stage_bounds(start_stage=None, end_stage=None, response=None):
    """
    Normalize optional start/end stage args for ObsPy plot/evalresp.

    Returns (start_stage, end_stage). Missing values keep ObsPy defaults
    (start=1, end=None). Raises ValueError when the range is invalid.
    """
    def _optional_int(value, name):
        if value is None or value == '':
            return None
        try:
            number = int(value)
        except (TypeError, ValueError):
            raise ValueError('%s must be an integer stage number' % name)
        if number < 1:
            raise ValueError('%s must be >= 1' % name)
        return number

    start = _optional_int(start_stage, 'start_stage')
    end = _optional_int(end_stage, 'end_stage')

    if response is not None:
        known = {item['number'] for item in response_plot_stages(response)}
        if known:
            first = min(known)
            last = max(known)
            # Stale Start/End from a previous response: clamp to this chain.
            if start is not None and start not in known:
                start = first
            if end is not None and end not in known:
                end = last

    if start is not None and end is not None and start > end:
        raise ValueError('start_stage must be <= end_stage')

    if start is None:
        start = 1
    return start, end


def is_full_stage_chain(response, start_stage, end_stage):
    """True when the plot range covers every response stage."""
    stages = response_plot_stages(response)
    if not stages:
        return True
    return (
        start_stage == stages[0]['number']
        and (end_stage is None or end_stage == stages[-1]['number'])
    )


def _stages_in_plot_range(response, start_stage, end_stage):
    selected = []
    for stage in getattr(response, 'response_stages', None) or []:
        number = getattr(stage, 'stage_sequence_number', None)
        try:
            number = int(number)
        except (TypeError, ValueError):
            continue
        if number < start_stage:
            continue
        if end_stage is not None and number > end_stage:
            continue
        selected.append(stage)
    return selected


def plot_marker_sensitivity(response, start_stage, end_stage):
    """
    Sensitivity ObsPy annotates on the Bode amplitude plot.

    Full-chain plots keep InstrumentSensitivity. Partial stage ranges use the
    product of StageGain values in the selected range (and the first defined
    StageGain frequency), so the marker matches the plotted stages.
    """
    from obspy.core.inventory.response import InstrumentSensitivity

    if is_full_stage_chain(response, start_stage, end_stage):
        return getattr(response, 'instrument_sensitivity', None)

    selected = _stages_in_plot_range(response, start_stage, end_stage)
    if not selected:
        return getattr(response, 'instrument_sensitivity', None)

    value = 1.0
    frequency = None
    have_gain = False
    for stage in selected:
        gain = getattr(stage, 'stage_gain', None)
        if gain is None:
            continue
        try:
            value *= float(gain)
        except (TypeError, ValueError):
            continue
        have_gain = True
        if frequency is None:
            gain_freq = getattr(stage, 'stage_gain_frequency', None)
            if gain_freq is not None:
                try:
                    frequency = float(gain_freq)
                except (TypeError, ValueError):
                    frequency = None

    if not have_gain:
        return getattr(response, 'instrument_sensitivity', None)

    if frequency is None:
        sens = getattr(response, 'instrument_sensitivity', None)
        if sens is not None and getattr(sens, 'frequency', None) is not None:
            try:
                frequency = float(sens.frequency)
            except (TypeError, ValueError):
                frequency = 1.0
        else:
            frequency = 1.0

    first = selected[0]
    last = selected[-1]
    input_units = getattr(first, 'input_units', None) or 'V'
    output_units = getattr(last, 'output_units', None) or 'V'
    return InstrumentSensitivity(
        value=value,
        frequency=frequency,
        input_units=input_units,
        output_units=output_units,
    )


def plot_frequency_limit(response, min_frequency=None):
    """Highest Max the plot will draw for this response and Min."""
    rate = _sample_rate_from_response(response)
    if rate is None or rate <= 0:
        limit = ABSOLUTE_MAX_HZ
    else:
        limit = min(float(rate), ABSOLUTE_MAX_HZ)
    if min_frequency not in (None, ''):
        min_hz = float(min_frequency)
        if 0 < min_hz < PLOT_MIN_WITHOUT_MAX_REDUCTION:
            limit = min(limit, PLOT_POINT_BUDGET * min_hz / 2.0)
            if limit < min_hz:
                limit = min_hz
    return limit


def plot_max_frequency(response, max_frequency=None, min_frequency=None):
    """Upper frequency actually drawn on the response plot."""
    limit = plot_frequency_limit(response, min_frequency)
    if max_frequency:
        requested = float(max_frequency)
        drawn = requested if requested > 0 else limit
        return min(drawn, limit)
    rate = _sample_rate_from_response(response)
    drawn = (rate / 2.0) if rate and rate > 0 else 100.0
    return min(drawn, limit)


def response_nyquist(response):
    """Nyquist frequency of the response, half its sample rate."""
    rate = _sample_rate_from_response(response)
    if rate and rate > 0:
        return rate / 2.0
    return None


def plot_sampling_rate(response, max_frequency=None, min_frequency=None):
    """Sampling rate passed to ObsPy so the axis ends at the drawn Max."""
    return 2.0 * plot_max_frequency(response, max_frequency, min_frequency)


def mark_response_nyquist(axes, drawn_max, true_nyquist):
    """Keep the dashed line on the response Nyquist, not on the Max cutoff."""
    if not drawn_max or drawn_max <= 0 or true_nyquist is None or true_nyquist <= 0:
        return
    if abs(true_nyquist - drawn_max) <= max(drawn_max, true_nyquist) * 1e-4:
        return
    inside = true_nyquist < drawn_max
    for ax in axes:
        color = 'C0'
        for line in list(ax.get_lines()):
            if line.get_linestyle() != '--':
                continue
            xs = line.get_xdata()
            if len(xs) and abs(float(xs[0]) - drawn_max) <= drawn_max * 1e-4:
                color = line.get_color()
                line.remove()
        if inside:
            ax.axvline(true_nyquist, ls='--', color=color, lw=1.5)


class ChannelUtils:

    @staticmethod
    def create_response_csv(response, folder, file_name, min_frequency=0.001, max_frequency=None,
                            fstep=0.1, instconfig=None, start_stage=None, end_stage=None):
        if not _is_response_object(response):
            raise ValueError(INVALID_STORED_RESPONSE)
        if response.instrument_polynomial is not None:
            return get_polynomial_resp_csv(response, folder, file_name)
        sampling_rate = plot_sampling_rate(response, max_frequency, min_frequency)
        plot_start, plot_end = parse_plot_stage_bounds(start_stage, end_stage, response)
        full_chain = is_full_stage_chain(response, plot_start, plot_end)
        plot_output = detect_plot_output(response, instconfig) if full_chain else 'DEF'
        marker_sensitivity = plot_marker_sensitivity(response, plot_start, plot_end)
        max_frequency = sampling_rate / 2.0

        min_frequency = float(min_frequency) if min_frequency is not None else 0.001
        max_frequency = float(max_frequency) if max_frequency is not None else 100.0
        # Use log-spaced frequencies (max 250 points) to avoid huge evalresp cost
        # for FIR-heavy responses (e.g. Sercel SlimWave: 33k coefficients).
        nfreqs = 250
        freqs = np.logspace(np.log10(min_frequency), np.log10(max_frequency), nfreqs)

        resp = response.get_evalresp_response_for_frequencies(
            freqs,
            output=plot_output,
            start_stage=plot_start,
            end_stage=plot_end)

        camp = np.abs(resp)
        rad2deg = 180./np.pi
        cang = np.angle(resp) * rad2deg

        os.makedirs(folder, exist_ok=True)
        sanitized_file_name = file_name.replace('/', '_').replace('\\', '_') + '.csv'
        file_path = os.path.join(folder, f'{sanitized_file_name}')

        import csv
        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                "Frequency [Hz]",
                amplitude_ylabel(plot_output, response, sensitivity=marker_sensitivity),
                "Phase [deg]",
            ])
            for i, freq in enumerate(freqs):
                # print(i, freq, camp[i], cang[i])
                writer.writerow([freq, camp[i], cang[i]])

        return sanitized_file_name

    @staticmethod
    def create_response_plot(response, folder, file_name, min_frequency=0.001, max_frequency=None,
                             instconfig=None, start_stage=None, end_stage=None):
        if not _is_response_object(response):
            raise ValueError(INVALID_STORED_RESPONSE)
        import matplotlib
        matplotlib.use('Agg')

        min_frequency = float(min_frequency) if min_frequency is not None else 0.001
        if response.instrument_polynomial is not None:
            # MTH: this label is not propagating to plot:
            return plot_polynomial_resp(response, label='Polynomial Response', axes=None, folder=folder, outfile=file_name)
        sampling_rate = plot_sampling_rate(response, max_frequency, min_frequency)
        plot_start, plot_end = parse_plot_stage_bounds(start_stage, end_stage, response)
        full_chain = is_full_stage_chain(response, plot_start, plot_end)
        # Partial stage ranges keep native stage units (DEF); full chain uses DISP/VEL/ACC.
        plot_output = detect_plot_output(response, instconfig) if full_chain else 'DEF'

        os.makedirs(folder, exist_ok=True)
        sanitized_file_name = file_name.replace('/', '_').replace('\\', '_') + '.png'
        file_path = os.path.join(folder, f'{sanitized_file_name}')

        # Create figure with larger size for better display in comparison mode
        import matplotlib.pyplot as plt
        fig = plt.figure(figsize=(12, 8))
        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212, sharex=ax1)
        # ObsPy always annotates instrument_sensitivity. For a stage subset,
        # temporarily swap in StageGain-based sensitivity so the markers match.
        original_sensitivity = response.instrument_sensitivity
        marker_sensitivity = plot_marker_sensitivity(response, plot_start, plot_end)
        # MTH: If the phase response looks funny, it's probably not a wrap issue,
        #      but an issue of missing the decimation delays/corrections for the FIR stages
        #      in the AROL lib.
        try:
            response.instrument_sensitivity = marker_sensitivity
            response.plot(
                min_frequency,
                output=plot_output,
                start_stage=plot_start,
                end_stage=plot_end,
                unwrap_phase=False,
                sampling_rate=sampling_rate,
                axes=[ax1, ax2],
                outfile=None)
        finally:
            response.instrument_sensitivity = original_sensitivity
        mark_response_nyquist(fig.axes, sampling_rate / 2.0, response_nyquist(response))
        apply_bode_axis_labels(
            fig, plot_output, response, plot_degrees=False, sensitivity=marker_sensitivity)
        save_bode_figure(fig, file_path)
        plt.close(fig)

        return sanitized_file_name

    @staticmethod
    def create_response_plot_difference(resp1, resp2, folder, file_name, min_frequency=0.001,
                                        max_frequency=None, instconfig=None):
        os.makedirs(folder, exist_ok=True)
        sanitized_file_name = file_name.replace('/', '_').replace('\\', '_') + '.png'
        file_path = os.path.join(folder, f'{sanitized_file_name}')

        sampling_rate = plot_sampling_rate(resp1, max_frequency, min_frequency)
        plot_output = detect_plot_output(resp1, instconfig)

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
                       outfile=file_path,
                       nyquist=response_nyquist(resp1))

        return sanitized_file_name

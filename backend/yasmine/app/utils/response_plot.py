# 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
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
# ****************************************************************************/


import copy
import html
import logging
import re
import numpy as np
from math import pi

from obspy.core.inventory.response import paz_to_sacpz_string
from obspy.core.util.obspy_types import ComplexWithUncertainties, ZeroSamplingRate
logger = logging.getLogger()

_ACCEL_UNIT_RE = re.compile(
    r"M/S\*\*2|M/\(S\*\*2\)|M/SEC\*\*2|M/\(SEC\*\*2\)|M/S/S|M/SEC/SEC",
    re.IGNORECASE,
)
_VEL_UNIT_RE = re.compile(
    r"^M/S$|^M/SEC$|^METERS/SECOND$|^METERS PER SECOND$",
    re.IGNORECASE,
)
_INSTCONFIG_ACCEL_RE = re.compile(r"STgroundAccel\b")
_INSTCONFIG_VEL_RE = re.compile(r"STgroundVel\b")
_INSTCONFIG_DISP_RE = re.compile(r"STgroundDisp\b")


def _get_unit_string(unit):
    if unit is None:
        return None
    if isinstance(unit, str):
        s = unit.strip()
        return s or None
    return getattr(unit, 'name', None) or getattr(unit, 'value', None) or str(unit)


def _units_to_evalresp_output(unit_str):
    """Map physical unit string to evalresp output code (DISP/VEL/ACC) or None."""
    if not unit_str:
        return None
    # RESP lookup strings: "M/S**2 - Acceleration..."
    token = unit_str.split(' - ', 1)[0].strip().upper()
    if _ACCEL_UNIT_RE.search(token):
        return 'ACC'
    if _VEL_UNIT_RE.match(token):
        return 'VEL'
    if token == 'M' or token == 'METERS':
        return 'DISP'
    return None


def _output_from_instconfig(instconfig):
    if not instconfig:
        return None
    if _INSTCONFIG_ACCEL_RE.search(instconfig):
        return 'ACC'
    if _INSTCONFIG_VEL_RE.search(instconfig):
        return 'VEL'
    if _INSTCONFIG_DISP_RE.search(instconfig):
        return 'DISP'
    return None


def _is_zero_number(value):
    try:
        return value is not None and float(value) == 0.0
    except (TypeError, ValueError):
        return False


def _unit_token(unit):
    text = _get_unit_string(unit)
    if not text:
        return None
    return text.split(' - ', 1)[0].strip().split()[0].lower()


_FILTER_STAGE_TYPES = (
    'PolesZerosResponseStage',
    'CoefficientsTypeResponseStage',
    'FIRResponseStage',
    'ResponseListResponseStage',
)

_NORM_RESP_FALLBACK = (
    'evalresp rejected this response while normalizing stage gains (norm_resp).'
    '<br>That code means one of these:'
    '<br>• InstrumentSensitivity (stage 0) is 0. Set it to any non-zero number, then recalculate. '
    'evalresp reads that value as a stage gain and stops while it is 0, before a new sensitivity can be computed.'
    '<br>• A StageGain value is 0, so the whole response is zero. Set that stage to its real gain.'
    '<br>• A stage has no StageGain, and there is no non-zero InstrumentSensitivity to copy onto it.'
    '<br>The computed sensitivity is the product of the stage gains at the sensitivity frequency.'
)

_CHECK_CHANNEL_FALLBACK = (
    'evalresp rejected the stage chain (check_channel).'
    '<br>That code means one of these:'
    '<br>• A stage input unit does not match the previous stage output unit.'
    '<br>• A Coefficients, FIR, or digital poles-and-zeros stage has no Decimation '
    '(input sample rate, factor, and offset).'
    '<br>• A stage has a Decimation but no filter, or a filter but no StageGain.'
    '<br>Make the units, filters, and decimation line up, then try again.'
)


def _esc(value):
    return html.escape(str(value), quote=False)


def _has_numeric(value):
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, (int, float)):
        return True
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


def _format_hz(freq):
    if not _has_numeric(freq):
        return ''
    return ' at %s Hz' % freq


def _stage_label(stage, fallback='A stage'):
    number = getattr(stage, 'stage_sequence_number', None)
    if number is None:
        return fallback
    return 'Stage %s' % number


def _stage_ref(stage):
    number = getattr(stage, 'stage_sequence_number', None)
    if number is None:
        return 'a stage'
    return 'stage %s' % number


def _gain_defined(stage):
    return (
        getattr(stage, 'stage_gain', None) is not None
        and getattr(stage, 'stage_gain_frequency', None) is not None
    )


def _has_decimation(stage):
    return (
        _has_numeric(getattr(stage, 'decimation_input_sample_rate', None))
        and _has_numeric(getattr(stage, 'decimation_factor', None))
    )


def _stage_type_name(stage):
    return type(stage).__name__


def _is_filter_stage(stage):
    return _stage_type_name(stage) in _FILTER_STAGE_TYPES


def _needs_decimation(stage):
    name = _stage_type_name(stage)
    if name in ('CoefficientsTypeResponseStage', 'FIRResponseStage'):
        return True
    if name == 'PolesZerosResponseStage':
        transfer = str(getattr(stage, 'pz_transfer_function_type', '') or '')
        return 'DIGITAL' in transfer.upper()
    return False


def _evalresp_function(error_text):
    text = (error_text or '').lower()
    if 'norm_resp' in text:
        return 'norm_resp'
    if 'check_channel' in text:
        return 'check_channel'
    return None


def _lines(*parts):
    return '<br>'.join(part for part in parts if part)


def _diagnose_norm_resp(response):
    """Match evalresp norm_resp: missing gain, then the first zero gain."""
    stages = list(getattr(response, 'response_stages', None) or [])
    sens = getattr(response, 'instrument_sensitivity', None)
    sens_value = getattr(sens, 'value', None) if sens is not None else None
    sens_is_zero = sens is not None and _is_zero_number(sens_value)
    sens_missing_or_zero = sens is None or sens_is_zero

    if stages and not _gain_defined(stages[0]) and (
            (len(stages) == 1 and sens_missing_or_zero)
            or (len(stages) == 2 and sens is None)):
        label = _stage_label(stages[0])
        return _lines(
            '%s has no StageGain (norm_resp: no stage gain defined, zero sensitivity).' % label,
            'evalresp needs a StageGain value and the frequency where that gain applies.',
            'It cannot invent one when InstrumentSensitivity is missing or 0.',
        )

    for stage in stages:
        if _is_zero_number(getattr(stage, 'stage_gain', None)):
            label = _stage_label(stage)
            return _lines(
                '%s gain is 0 (norm_resp: zero stage gain).' % label,
                'A zero stage gain makes the whole response zero, so evalresp will not normalize it.',
                'Set this StageGain to the stage\'s real gain. '
                'Overall sensitivity is the product of every stage gain.',
            )

    if sens_is_zero:
        where = _format_hz(getattr(sens, 'frequency', None))
        return _lines(
            'Stage 0 sensitivity is 0%s (norm_resp: zero stage gain).' % where,
            'Set InstrumentSensitivity to any non-zero number, then recalculate.',
            'evalresp reads that value as stage 0 and stops while it is 0, '
            'before a new sensitivity can be computed.',
            'The computed sensitivity is the product of the stage gains at the sensitivity frequency.',
        )
    return None


def _diagnose_check_channel(response):
    """Match evalresp check_channel: gain, units, then required decimation."""
    previous = None
    for stage in getattr(response, 'response_stages', None) or []:
        name = _stage_type_name(stage)
        if name == 'ResponseStage':
            if _has_decimation(stage):
                return _lines(
                    '%s has a Decimation but no filter '
                    '(check_channel: decimation blockette with no associated filter).' % _stage_label(stage),
                    'Decimation belongs on a PolesZeros, Coefficients, or FIR stage.',
                )
            continue

        if _is_filter_stage(stage) and not _gain_defined(stage):
            return _lines(
                '%s has a filter but no StageGain (check_channel: gain blockette is missing).' % _stage_label(stage),
                'Add StageGain Value and Frequency. evalresp requires a gain after every filter.',
            )

        incoming = _unit_token(getattr(stage, 'input_units', None))
        outgoing = _unit_token(getattr(stage, 'output_units', None))
        if previous and incoming and previous != incoming:
            return _lines(
                'Units mismatch at %s: %s followed by %s (check_channel).' % (
                    _stage_ref(stage), _esc(previous), _esc(incoming),
                ),
                'This stage\'s input units must be the same as the previous stage\'s output units.',
                'evalresp evaluates only a response whose units form one chain from the sensor to the output.',
            )
        if _is_filter_stage(stage) and _needs_decimation(stage) and not _has_decimation(stage):
            return _lines(
                '%s has no Decimation '
                '(check_channel: required decimation blockette for IIR or FIR filter missing).' % _stage_label(stage),
                'A Coefficients, FIR, or digital poles-and-zeros stage needs a Decimation '
                'with input sample rate, factor, and offset.',
                'evalresp cannot evaluate a digital filter without a sample rate.',
            )
        if outgoing:
            previous = outgoing
    return None


def diagnose_evalresp_response(response, error_text=''):
    """Explain an evalresp 'Illegal RESP format' from the response itself.

    ObsPy maps every evalresp status -5 to that one string. The C library's
    own reason (zero stage gain, units mismatch, missing decimation) is only
    printed to stderr. ``error_text`` selects norm_resp or check_channel,
    because those functions run in that order and fail for different reasons.
    """
    if response is None:
        return None
    function = _evalresp_function(error_text)
    if function != 'check_channel':
        reason = _diagnose_norm_resp(response)
        if reason or function == 'norm_resp':
            return reason
    return _diagnose_check_channel(response)


def explain_illegal_resp_format(error_text, response=None):
    """Detailed user-facing text for ObsPy's Illegal RESP format error."""
    reason = diagnose_evalresp_response(response, error_text)
    if reason:
        return reason
    function = _evalresp_function(error_text)
    if function == 'check_channel':
        return _CHECK_CHANNEL_FALLBACK
    if function == 'norm_resp':
        return _NORM_RESP_FALLBACK
    return _NORM_RESP_FALLBACK + '<br><br>' + _CHECK_CHANNEL_FALLBACK


def format_response_failure(error, response=None, action='generate plot'):
    """User-facing response error. Prefer the evalresp reason over the generic code."""
    text = str(error).strip() or 'Unknown error'
    if 'illegal resp format' in text.lower():
        return 'Cannot %s.<br>%s' % (action, explain_illegal_resp_format(text, response))
    return 'Cannot %s.<br>%s' % (action, text)


def format_plot_failure(error, response=None):
    """User-facing plot error. Prefer the evalresp reason over the generic code."""
    return format_response_failure(error, response, 'generate plot')


def format_sensitivity_failure(error, response=None):
    """User-facing Recalculate Sensitivity error."""
    return format_response_failure(error, response, 'recalculate sensitivity')


def detect_plot_output(response, instconfig=None):
    """Choose evalresp output (DISP/VEL/ACC/DEF). Response units win over the NRL name."""
    if response is not None:
        sens = getattr(response, 'instrument_sensitivity', None)
        if sens:
            out = _units_to_evalresp_output(_get_unit_string(sens.input_units))
            if out:
                return out
        stages = getattr(response, 'response_stages', None) or []
        if stages:
            out = _units_to_evalresp_output(_get_unit_string(stages[0].input_units))
            if out:
                return out

    from_instconfig = _output_from_instconfig(instconfig)
    if from_instconfig:
        return from_instconfig
    return 'DEF'


# evalresp DISP/VEL/ACC is the ground-motion unit the transfer function is
# relative to. The plotted magnitude is output/input (counts per m/s), not
# the ground motion itself.
_GROUND_MOTION_UNIT = {
    'VEL': 'm/s',
    'ACC': 'm/s²',
    'DISP': 'm',
}

_OUTPUT_TYPE_SUFFIX = {
    'VEL': 'velocity',
    'ACC': 'acceleration',
    'DISP': 'displacement',
}

BODE_FIGURE_SAVEFIG_KWARGS = {'dpi': 120, 'bbox_inches': 'tight', 'pad_inches': 0.12}
_BODE_SUBPLOTS_ADJUST = {'hspace': 0.02, 'top': 0.87, 'right': 0.82, 'left': 0.10}


def save_bode_figure(fig, file_path):
    """Save Bode figure with axis labels included in the image bounds."""
    fig.savefig(file_path, **BODE_FIGURE_SAVEFIG_KWARGS)


def _canonical_unit_token(unit_str):
    """Short unit token for labels, e.g. 'COUNTS - Digital Counts' -> counts."""
    if not unit_str:
        return None
    token = unit_str.split(' - ', 1)[0].strip().lower()
    return token or None


def _response_output_token(response, sensitivity=None):
    sens = sensitivity
    if sens is None and response is not None:
        sens = getattr(response, 'instrument_sensitivity', None)
    if sens:
        token = _canonical_unit_token(_get_unit_string(sens.output_units))
        if token:
            return token
    stages = getattr(response, 'response_stages', None) or []
    if stages:
        return _canonical_unit_token(_get_unit_string(getattr(stages[-1], 'output_units', None)))
    return None


def amplitude_ylabel(plot_output, response=None, sensitivity=None):
    """Y-axis label for Bode amplitude subplot.

    When ``sensitivity`` is given (e.g. stage-range marker sensitivity), its
    units win over ``response.instrument_sensitivity``.
    """
    code = (plot_output or 'DEF').upper()
    ground = _GROUND_MOTION_UNIT.get(code)
    if ground:
        output = _response_output_token(response, sensitivity) or 'counts'
        return f'Amplitude [{output}/{ground}]'
    sens = sensitivity
    if sens is None and response is not None:
        sens = getattr(response, 'instrument_sensitivity', None)
    if sens:
        out_u = _canonical_unit_token(_get_unit_string(sens.output_units))
        in_u = _canonical_unit_token(_get_unit_string(sens.input_units))
        if out_u and in_u:
            return f'Amplitude [{out_u}/{in_u}]'
    return 'Amplitude'


def diff_amplitude_ylabel(plot_output):
    """Y-axis label for amplitude-difference Bode subplot."""
    code = (plot_output or 'DEF').upper()
    label = 'Amplitude difference [dB]'
    suffix = _OUTPUT_TYPE_SUFFIX.get(code)
    if suffix:
        return f'{label} ({suffix})'
    return label


def apply_bode_axis_labels(fig, plot_output, response=None, *, plot_degrees=False,
                           sensitivity=None):
    """Set axis labels and layout after ObsPy response.plot with external axes."""
    import matplotlib.pyplot as plt

    fig.subplots_adjust(**_BODE_SUBPLOTS_ADJUST)
    ax1, ax2 = fig.axes[:2]
    plt.setp(ax1.get_xticklabels(), visible=False)
    ax1.set_ylabel(amplitude_ylabel(plot_output, response, sensitivity=sensitivity))
    ax1.grid(True)
    ax2.set_xlabel('Frequency [Hz]')
    ax2.set_ylabel('Phase [degrees]' if plot_degrees else 'Phase [rad]')
    ax2.grid(True)


def _prepare_paz_for_sacpz(paz):
    """
    Fix None uncertainties in poles/zeros so to_radians_per_second() won't fail.
    ObsPy does: x.upper_uncertainty * twopi - fails when None.
    """
    def fix_uncertainties(items):
        result = []
        for x in items:
            up = getattr(x, 'upper_uncertainty', None)
            low = getattr(x, 'lower_uncertainty', None)
            up = 0.0 if up is None else up
            low = 0.0 if low is None else low
            result.append(ComplexWithUncertainties(
                x.real, x.imag,
                upper_uncertainty=up, lower_uncertainty=low))
        return result

    paz = copy.deepcopy(paz)
    paz.poles = fix_uncertainties(paz.poles)
    paz.zeros = fix_uncertainties(paz.zeros)
    if paz.normalization_factor is None:
        paz.normalization_factor = 1.0
    return paz


def _prepare_sensitivity_for_sacpz(response):
    """Fix None instrument_sensitivity.value (required for constant = norm * sens)."""
    if response.instrument_sensitivity is None:
        return
    v = response.instrument_sensitivity.value
    sens_val = getattr(v, 'value', v) if v is not None else None
    if sens_val is None:
        sens_val = 1.0
        for stage in response.response_stages or []:
            gain = getattr(stage, 'stage_gain', None)
            if gain:
                sens_val *= float(gain)
        response.instrument_sensitivity.value = sens_val


def plot_diff_resp(response, resp2, min_freq, output=None, start_stage=None,
                   end_stage=None, label=None, axes=None, sampling_rate=None,
                   unwrap_phase=False, plot_degrees=False, show=True, outfile=None,
                   nyquist=None):
    """
    Show bode plot of instrument response.

    :type min_freq: float
    :param min_freq: Lowest frequency to plot.
    :type output: str
    :param output: Output units. One of:

            ``"DISP"``
                displacement
            ``"VEL"``
                velocity
            ``"ACC"``
                acceleration

    :type start_stage: int, optional
    :param start_stage: Stage sequence number of first stage that will be
        used (disregarding all earlier stages).
    :type end_stage: int, optional
    :param end_stage: Stage sequence number of last stage that will be
        used (disregarding all later stages).
    :type label: str
    :param label: Label string for legend.
    :type axes: list of 2 :class:`matplotlib.axes.Axes`
    :param axes: List/tuple of two axes instances to plot the
        amplitude/phase spectrum into. If not specified, a new figure is
        opened.
    :type sampling_rate: float
    :param sampling_rate: Manually specify sampling rate of time series.
        If not given it is attempted to determine it from the information
        in the individual response stages.  Does not influence the spectra
        calculation, if it is not known, just provide the highest frequency
        that should be plotted times two.
    :type unwrap_phase: bool
    :param unwrap_phase: Set optional phase unwrapping using NumPy.
    :type plot_degrees: bool
    :param plot_degrees: if ``True`` plot bode in degrees
    :type show: bool
    :param show: Whether to show the figure after plotting or not. Can be
        used to do further customization of the plot before showing it.
    :type outfile: str
    :param outfile: Output file path to directly save the resulting image
        (e.g. ``"/tmp/image.png"``). Overrides the ``show`` option, image
        will not be displayed interactively. The given path/filename is
        also used to automatically determine the output format. Supported
        file formats depend on your matplotlib backend.  Most backends
        support png, pdf, ps, eps and svg. Defaults to ``None``.

    .. rubric:: Basic Usage

    >>> from obspy import read_inventory
    >>> resp = read_inventory()[0][0][0].response
    >>> resp.plot(0.001, output="VEL")  # doctest: +SKIP

    .. plot::

        from obspy import read_inventory
        resp = read_inventory()[0][0][0].response
        resp.plot(0.001, output="VEL")
    """
    import matplotlib.pyplot as plt
    from matplotlib.transforms import blended_transform_factory

    # detect sampling rate from response stages
    if sampling_rate is None:
        for stage in response.response_stages[::-1]:
            if (stage.decimation_input_sample_rate is not None and
                    stage.decimation_factor is not None):
                sampling_rate = (stage.decimation_input_sample_rate /
                                 stage.decimation_factor)
                break
        else:
            msg = ("Failed to autodetect sampling rate of channel from "
                   "response stages. Please manually specify parameter "
                   "`sampling_rate`")
            raise Exception(msg)
    if sampling_rate == 0:
        msg = "Can not plot response for channel with sampling rate `0`."
        raise ZeroSamplingRate(msg)

    max_freq = sampling_rate / 2.0
    '''
    t_samp = 1.0 / sampling_rate
    nyquist = sampling_rate / 2.0
    nfft = int(sampling_rate / min_freq)

    cpx_response, freq = response.get_evalresp_response(
        t_samp=t_samp, nfft=nfft, output=output, start_stage=start_stage,
        end_stage=end_stage)
    '''

    nfreqs = 200
    n1 = np.log10(min_freq)
    n2 = np.log10(max_freq)
    freqs = np.array(np.logspace(n1, n2, nfreqs))

    if output is None:
        output = detect_plot_output(response)
    out2 = detect_plot_output(resp2)
    if out2 and out2 != output and output != 'DEF':
        logger.warning(
            'Response diff plot: resp2 output %s differs from resp1 %s; using %s',
            out2, output, output,
        )

    resp1 = response
    x1 = resp1.get_evalresp_response_for_frequencies(
        freqs, output=output, start_stage=start_stage, end_stage=end_stage)
    x2 = resp2.get_evalresp_response_for_frequencies(
        freqs, output=output, start_stage=start_stage, end_stage=end_stage)
    x1_mag = np.abs(x1)
    x1_pha = np.angle(x1, deg=plot_degrees)
    x2_mag = np.abs(x2)
    x2_pha = np.angle(x2, deg=plot_degrees)

    diff_mag = np.full(freqs.shape, np.nan, dtype=float)
    diff_pha = np.full(freqs.shape, np.nan, dtype=float)
    for i, f in enumerate(freqs):
        if x2_mag[i] > 0 and x1_mag[i] > 0:
            diff_mag[i] = 20 * (np.log10(x1_mag[i]) - np.log10(x2_mag[i]))
            diff_pha[i] = x1_pha[i] - x2_pha[i]
    if unwrap_phase:
        if plot_degrees:
            diff_pha = np.rad2deg(np.unwrap(np.deg2rad(diff_pha)))
        else:
            diff_pha = np.unwrap(diff_pha)
    else:
        diff_pha = _wrap_phase(diff_pha, plot_degrees)

    if axes:
        ax1, ax2 = axes
        fig = ax1.figure
    else:
        fig = plt.figure(figsize=(12, 8))
        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212, sharex=ax1)

    label_kwarg = {}
    if label is not None:
        label_kwarg['label'] = label

    # plot amplitude response
    lw = 1.5
    marker = "."
    # lines = ax1.loglog(freq, abs(cpx_response), lw=lw, **label_kwarg)
    # lines = ax1.loglog(freqs, diff_mag, lw=lw, **label_kwarg)
    # lines = ax1.semilogx(freqs, diff_mag, lw=lw, **label_kwarg)
    lines = ax1.semilogx(freqs, diff_mag, marker, **label_kwarg)

    color = lines[0].get_color()
    if 0 and response.instrument_sensitivity:
        trans_above = blended_transform_factory(ax1.transData,
                                                ax1.transAxes)
        trans_right = blended_transform_factory(ax1.transAxes,
                                                ax1.transData)
        arrowprops = dict(
            arrowstyle="wedge,tail_width=1.4,shrink_factor=0.8", fc=color)
        bbox = dict(boxstyle="round", fc="w")
        if response.instrument_sensitivity.frequency:
            ax1.annotate("%.1g" % response.instrument_sensitivity.frequency,
                         (response.instrument_sensitivity.frequency, 1.0),
                         xytext=(response.instrument_sensitivity.frequency,
                                 1.1),
                         xycoords=trans_above, textcoords=trans_above,
                         ha="center", va="bottom",
                         arrowprops=arrowprops, bbox=bbox)
        if response.instrument_sensitivity.value:
            ax1.annotate("%.1e" % response.instrument_sensitivity.value,
                         (1.0, response.instrument_sensitivity.value),
                         xytext=(1.05, response.instrument_sensitivity.value),
                         xycoords=trans_right, textcoords=trans_right,
                         ha="left", va="center",
                         arrowprops=arrowprops, bbox=bbox)

    # plot phase response
    # phase = np.angle(cpx_response, deg=plot_degrees)
    # if unwrap_phase and not plot_degrees:
    # phase = np.unwrap(phase)
    # ax2.semilogx(freq, phase, color=color, lw=lw)
    # ax2.semilogx(freqs, diff_pha, color=color, lw=lw)
    ax2.semilogx(freqs, diff_pha, color=color, marker=marker)

    # Dashed line is the response Nyquist, drawn only inside the shown range.
    if nyquist and 0 < nyquist <= max_freq * (1 + 1e-4):
        for ax in (ax1, ax2):
            ax.axvline(nyquist, ls="--", color=color, lw=lw)

    # only do adjustments if we initialized the figure in here
    if not axes:
        _adjust_bode_plot_figure(fig, show=False,
                                 plot_degrees=plot_degrees, plot_output=output)

    if outfile:
        save_bode_figure(fig, outfile)
    else:
        print("Now show the plot show=%s" % show)
        if show:
            plt.show()

    return fig


def _wrap_phase(diff, degrees):
    """Fold a phase difference into (-180, 180] degrees or (-pi, pi] radians.

    A raw subtraction of two wrapped phases jumps by a full turn. That jump
    is not an instrument difference, and a Bode axis clipped at ±180 hides it.
    NaN stays NaN so a zero-magnitude sample does not become a line.
    """
    span = 360.0 if degrees else (2.0 * pi)
    half = span / 2.0
    wrapped = (diff + half) % span - half
    return np.where(np.isnan(diff), np.nan, wrapped)


def _adjust_bode_plot_figure(fig, plot_degrees=False, grid=True, show=True, plot_output=None):
    """
    Helper function to do final adjustments to Bode plot figure.
    """
    import matplotlib.pyplot as plt
    # make more room in between subplots for the ylabel of right plot
    fig.subplots_adjust(**_BODE_SUBPLOTS_ADJUST)
    ax1, ax2 = fig.axes[:2]
    # workaround for older matplotlib versions
    try:
        ax1.legend(loc="lower center", ncol=3, fontsize='small')
    except TypeError:
        leg_ = ax1.legend(loc="lower center", ncol=3)
        leg_.prop.set_size("small")
    plt.setp(ax1.get_xticklabels(), visible=False)
    ax1.set_ylabel(diff_amplitude_ylabel(plot_output))
    # I don't know where get_ylim() is getting this from but it's clearly wrong
    minmax1 = ax1.get_ylim()
    # print(minmax1)
    ymax = minmax1[1] * 2
    # ax1.set_ylim(top=minmax1[1] * 5)
    ax1.set_ylim(ymin=-ymax, ymax=ymax)

    # print("MTH: adjust_bode_plot: plot_degrees=[%s] grid=[%s] show=[%s] ax1 ylim=%f" % \
    # (plot_degrees, grid, show, minmax1[1]*5))
    ax1.grid(True)
    ax2.set_xlabel('Frequency [Hz]')
    if plot_degrees:
        # degrees bode plot
        ax2.set_ylabel('Phase difference [deg]')
        ax2.set_yticks(np.arange(-180, 180, 30))
        ax2.set_yticklabels(np.arange(-180, 180, 30))
        ax2.set_ylim(-180, 180)
    else:
        # radian bode plot
        plt.setp(ax2.get_yticklabels()[-1], visible=False)
        ax2.set_ylabel('Phase [rad]')
        minmax2 = ax2.yaxis.get_data_interval()
        yticks2 = np.arange(minmax2[0] - minmax2[0] % (pi / 2),
                            minmax2[1] - minmax2[1] % (pi / 2) + pi, pi / 2)
        ax2.set_yticks(yticks2)
        ax2.set_yticklabels([_pitick2latex(x) for x in yticks2])
    ax2.grid(True)

    if show:
        plt.show()


def _pitick2latex(x):
    """
    Helper function to convert a float that is a multiple of pi/2
    to a latex string.
    """
    # safety check, if no multiple of pi/2 return normal representation
    if x % (pi / 2) != 0:
        return "%#.3g" % x
    string = "$"
    if x < 0:
        string += "-"
    if x / pi % 1 == 0:
        x = abs(int(x / pi))
        if x == 0:
            return "$0$"
        elif x == 1:
            x = ""
        string += r"%s\pi$" % x
    else:
        x = abs(int(2 * x / pi))
        if x == 1:
            x = ""
        string += r"\frac{%s\pi}{2}$" % x
    return string


def polynomial_chain_gain(response):
    """Product of stage gains after the sensor polynomial.

    The builder scales InstrumentPolynomial by the datalogger chain only.
    """
    from obspy.core.inventory.response import PolynomialResponseStage

    gain = 1.0
    after_polynomial = False
    for stage in getattr(response, 'response_stages', None) or []:
        if isinstance(stage, PolynomialResponseStage):
            after_polynomial = True
            continue
        if not after_polynomial:
            continue
        value = getattr(stage, 'stage_gain', None)
        if value:
            gain *= float(value)
    return gain or 1.0


def _polynomial_output_sweep_bounds(poly, default_min=-20., default_max=20.):
    """Prefer approximation bounds when they look like an output sweep range."""
    try:
        lower = float(getattr(poly, 'approximation_lower_bound', None))
        upper = float(getattr(poly, 'approximation_upper_bound', None))
    except (TypeError, ValueError):
        return default_min, default_max
    if lower != lower or upper != upper or lower >= upper:
        return default_min, default_max
    units = str(getattr(poly, 'output_units', '') or '').upper()
    # Approximation bounds are usually in input space (degC, strain, …).
    # Only reuse them as the output sweep when units look like volts.
    if units in ('V', 'VOLT', 'VOLTS'):
        pad = max((upper - lower) * 0.05, 0.1)
        return lower - pad, upper + pad
    return default_min, default_max


def plot_polynomial_resp(response, label=None, axes=None, folder=None, outfile=None,
                         vmin=None, vmax=None, dv=0.10):
    """
        Plot polynomial response
        The way that polynomial responses are calculated is a bit "bassackwards":
        Given a range of inputs (e.g., temperatures), we use the polynomial coefficients
        to calculate what the corresponding outputs (volts or counts) would be.
        We plot input_units on the x-axis and output_units on the y-axis to form y=y(x).

        Will produce 2 subplots: 1. xy-plot of y=output_units (e.g., Volts) vs x=input_units (e.g., degC)
                                 2. xy-plot of y=output_units (e.g., Counts)vs x=input_units (e.g., degC)

        For a MCLAUREN polynomial response, plot 1 comes from the PolynomialResponseStage (e.g., first stage)
              while plot 2 comes from the InstrumentPolynomial (overall response with net gain included in coeffs)

    :param response: channel polynomial response
    :type output: ObsPy response object

    Default sweep is ±20 V (legacy). When *vmin*/*vmax* are omitted and the first
    PolynomialResponseStage exposes approximation_lower/upper_bound in the same
    units as the stage output (e.g. volts), those bounds drive the sweep instead.
    """

    from obspy.core.inventory.response import PolynomialResponseStage, InstrumentPolynomial
    import matplotlib.pyplot as plt
    import os

    if not response.instrument_polynomial or not isinstance(response.response_stages[0], PolynomialResponseStage):
        logger.error("plot_polynomial_resp: response does not contain instrument_polynomial ",
                     "and/or PolynomialResponseStage")
        return None

    file_name = outfile
    os.makedirs(folder, exist_ok=True)
    sanitized_file_name = file_name.replace('/', '_').replace('\\', '_') + '.png'
    file_path = os.path.join(folder, f'{sanitized_file_name}')
    outfile = file_path

    # InstrumentPolynomial coefficients are already scaled by the datalogger
    # gain. Use that same product, not the sensor stage as well.
    net_gain = polynomial_chain_gain(response)

    def _coeff_val(c):
        v = getattr(c, 'value', c)
        return float(v) if v is not None else 0.0

    poly = response.response_stages[0]
    if vmin is None or vmax is None:
        vmin, vmax = _polynomial_output_sweep_bounds(poly, default_min=-20., default_max=20.)
    xlabel = poly.input_units
    ylabel = poly.output_units

    # MTH: We need a min/max in the *output* space (e.g., volts) to step through
    #      Otherwise we'll be calculating wild values out of range
    #      Add a little bit to vmax to it gets included in the array
    volts = np.arange(vmin, vmax+dv/10., dv)

    # Load x=temp = f(y=volts) // the measured thing might not be "temp", it doesn't matter
    x1 = []
    y1 = []
    for volt in volts:
        temp = 0.
        for i, c in enumerate(poly.coefficients):
            temp += _coeff_val(c) * np.power(volt, i)
        if temp >= poly.approximation_lower_bound and temp <= poly.approximation_upper_bound:
            x1.append(temp)
            y1.append(volt)

    # Load x=temp = f(y=counts)
    poly = response.instrument_polynomial
    y2label = poly.output_units
    x2 = []
    y2 = []
    for volt in volts:
        temp = 0.
        count = volt * net_gain
        for i, c in enumerate(poly.coefficients):
            temp += _coeff_val(c) * np.power(count, i)
        if temp >= poly.approximation_lower_bound and temp <= poly.approximation_upper_bound:
            x2.append(temp)
            y2.append(count)

    if axes:
        ax1, ax2 = axes
        fig = ax1.figure
    else:
        fig = plt.figure(figsize=(12, 8))
        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212, sharex=ax1)

    label_kwarg = {}
    # if label is not None:
    #   label_kwarg['label'] = label

    plt.suptitle(label)
    plt.xlabel(xlabel)
    ax1.set_ylabel(ylabel)
    ax2.set_ylabel(y2label)
    ax2.ticklabel_format(axis='y', style='sci', useMathText=True, scilimits=(0, 0))

    lw = 1.5
    marker = "."
    color = 'red'
    lines = ax1.plot(x1, y1, marker=marker, color=color, **label_kwarg)

    # color = lines[0].get_color()
    lines = ax2.plot(x2, y2, color=color, marker=marker)

    plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=0.3)

    show = 1
    if outfile:
        save_bode_figure(fig, outfile)
    else:
        if show:
            plt.show()

    # return fig
    return sanitized_file_name


def get_polynomial_resp_csv(response, folder=None, outfile=None,
                            vmin=-20., vmax=20., dv=0.10):
    """
    """
    from obspy.core.inventory.response import PolynomialResponseStage, InstrumentPolynomial
    import os

    if not response.instrument_polynomial or not isinstance(response.response_stages[0], PolynomialResponseStage):
        logger.error("plot_polynomial_resp: response does not contain instrument_polynomial ",
                     "and/or PolynomialResponseStage")
        return None

    file_name = outfile
    os.makedirs(folder, exist_ok=True)
    sanitized_file_name = file_name.replace('/', '_').replace('\\', '_') + '.csv'
    file_path = os.path.join(folder, f'{sanitized_file_name}')
    outfile = file_path

    # InstrumentPolynomial coefficients are already scaled by the datalogger
    # gain. Use that same product, not the sensor stage as well.
    net_gain = polynomial_chain_gain(response)

    def _coeff_val(c):
        v = getattr(c, 'value', c)
        return float(v) if v is not None else 0.0

    poly = response.response_stages[0]

    # MTH: We need a min/max in the *output* space (e.g., volts) to step through
    #      Otherwise we'll be calculating wild values out of range
    volts = np.arange(vmin, vmax, dv)

    # Load x=temp = f(y=volts) // the measured thing might not be "temp", it doesn't matter
    x = []
    y1 = []
    for volt in volts:
        temp = 0.
        for i, c in enumerate(poly.coefficients):
            temp += _coeff_val(c) * np.power(volt, i)
        if temp >= poly.approximation_lower_bound and temp <= poly.approximation_upper_bound:
            # print("V:%.3f     T:%.2f" % (volt, temp))
            x.append(temp)
            y1.append(volt)

    # Load x=temp = f(y=counts)
    poly = response.instrument_polynomial
    y2 = []
    for volt in volts:
        temp = 0.
        count = volt * net_gain
        for i, c in enumerate(poly.coefficients):
            temp += _coeff_val(c) * np.power(count, i)
        if temp >= poly.approximation_lower_bound and temp <= poly.approximation_upper_bound:
            y2.append(count)

    import csv
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Signal", "Volts", "Counts"])
        for i in range(len(x)):
            writer.writerow([x[i], y1[i], y2[i]])

    return sanitized_file_name


def print_polynomial_resp(response):
    ip = response.instrument_polynomial
    ret = (
      "Channel Response\n"
      "\tPolynomial Response Type:{approx_type}\n"
      "\tFrom {input_units} ({input_units_description}) to "
      "{output_units} ({output_units_description})\n"
      "\tApproximation Range:{approx_lower} to {approx_upper}\n"
      "\t{stages} stages:\n{stage_desc}").format(
      approx_type=ip.approximation_type,
      approx_lower=ip.approximation_lower_bound,
      approx_upper=ip.approximation_upper_bound,
      input_units=ip.input_units,
      input_units_description=ip.input_units_description,
      output_units=ip.output_units,
      output_units_description=ip.output_units_description,
      stages=len(response.response_stages),
      stage_desc="\n".join(
          ["\t\tStage %i: %s from %s to %s,"
           " gain: %s" % (
               i.stage_sequence_number, i.__class__.__name__,
               i.input_units, i.output_units,
               ("%g" % i.stage_gain) if i.stage_gain else "UNKNOWN")
           for i in response.response_stages]))

    return ret


INVALID_STORED_RESPONSE = (
    'Stored channel response is damaged. Select the response again.'
)


def _is_response_object(response):
    return not isinstance(response, str) and hasattr(response, 'instrument_polynomial')


def polynomial_or_polezero_response(response):
    if not _is_response_object(response):
        return INVALID_STORED_RESPONSE
    response_str = str(response)
    if response.instrument_polynomial:
        try:
            to_return = print_polynomial_resp(response)
        except Exception:
            to_return = 'Polynomial Response is Broken'
    else:
        try:
            # ObsPy's get_sacpz fails when: pole/zero uncertainties are None,
            # or paz.normalization_factor or instrument_sensitivity.value is None.
            # Prepare data and use paz_to_sacpz_string directly.
            paz = _prepare_paz_for_sacpz(response.get_paz())
            _prepare_sensitivity_for_sacpz(response)
            polezero_stage_str = paz_to_sacpz_string(paz, response.instrument_sensitivity)
            to_return = '\n\nPolezeroStage\n'.join([response_str, polezero_stage_str])
        except Exception as e:
            to_return = str(e)
    return to_return

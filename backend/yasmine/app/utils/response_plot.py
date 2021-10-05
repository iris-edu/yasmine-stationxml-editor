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


import logging
import numpy as np
from math import pi

from obspy.core.util.obspy_types import ZeroSamplingRate
logger = logging.getLogger()


def plot_diff_resp(response, resp2, min_freq, output="VEL", start_stage=None,
                   end_stage=None, label=None, axes=None, sampling_rate=None,
                   unwrap_phase=False, plot_degrees=False, show=True, outfile=None):
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

    nyquist = sampling_rate / 2.0
    '''
    t_samp = 1.0 / sampling_rate
    nyquist = sampling_rate / 2.0
    nfft = int(sampling_rate / min_freq)

    cpx_response, freq = response.get_evalresp_response(
        t_samp=t_samp, nfft=nfft, output=output, start_stage=start_stage,
        end_stage=end_stage)
    '''

    max_freq = sampling_rate / 2
    nfreqs = 200
    n1 = np.log10(min_freq)
    n2 = np.log10(max_freq)
    freqs = np.array(np.logspace(n1, n2, nfreqs))

    resp1 = response
    x1 = resp1.get_evalresp_response_for_frequencies(freqs, output='VEL', start_stage=None, end_stage=None)
    x2 = resp2.get_evalresp_response_for_frequencies(freqs, output='VEL', start_stage=None, end_stage=None)
    x1_mag = np.abs(x1)
    x1_pha = np.angle(x1, deg=plot_degrees)
    x2_mag = np.abs(x2)
    x2_pha = np.angle(x2, deg=plot_degrees)

    diff_mag = np.zeros_like(freqs)
    diff_pha = np.zeros_like(freqs)
    for i, f in enumerate(freqs):
        # print("%3d %f %f %f" % (i, f, x1_mag[i], x2_mag[i]))
        if x2_mag[i] > 0 and x1_mag[i] > 0:
            diff_mag[i] = 20 * (np.log10(x1_mag[i]) - np.log10(x2_mag[i]))
        else:
            diff_mag[i] = -10
        # if i == 10:
        # diff_mag[i] = 1000

        diff_pha[i] = x1_pha[i] - x2_pha[i]
        # print("%3d %f %f %f" % (i, f, diff_mag[i], diff_pha[i]))

    if axes:
        ax1, ax2 = axes
        fig = ax1.figure
    else:
        fig = plt.figure()
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

    # plot nyquist frequency
    for ax in (ax1, ax2):
        ax.axvline(nyquist, ls="--", color=color, lw=lw)

    # only do adjustments if we initialized the figure in here
    if not axes:
        _adjust_bode_plot_figure(fig, show=False,
                                 plot_degrees=plot_degrees)

    if outfile:
        fig.savefig(outfile)
    else:
        print("Now show the plot show=%s" % show)
        if show:
            plt.show()

    return fig


def _adjust_bode_plot_figure(fig, plot_degrees=False, grid=True, show=True):
    """
    Helper function to do final adjustments to Bode plot figure.
    """
    import matplotlib.pyplot as plt
    # make more room in between subplots for the ylabel of right plot
    fig.subplots_adjust(hspace=0.02, top=0.87, right=0.82)
    ax1, ax2 = fig.axes[:2]
    # workaround for older matplotlib versions
    try:
        ax1.legend(loc="lower center", ncol=3, fontsize='small')
    except TypeError:
        leg_ = ax1.legend(loc="lower center", ncol=3)
        leg_.prop.set_size("small")
    plt.setp(ax1.get_xticklabels(), visible=False)
    # ax1.set_ylabel('Amplitude')
    ax1.set_ylabel('Amplitude Diff [dB]')
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
        ax2.set_ylabel('Phase Diff [deg]')
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


def plot_polynomial_resp(response, label=None, axes=None, folder=None, outfile=None,
                         vmin=-20., vmax=20., dv=0.10):
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

    MTH: By default, plot_polynomial_resp will step over voltage from -20V to +20V
         with dV step=0.1V, but the final plot xy ranges will be set by
         the input (x-axis) range: poly.approximation_lower_bound - upper_bound
         However, I left vmin/vmax/dv configurable in case a calling function wants
         to control this to limit plot range (somehow).
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

    # We'll use the overall gain to scale between Volts and Counts
    net_gain = 1.
    for i, stage in enumerate(response.response_stages):
        if stage.stage_gain:
            net_gain *= stage.stage_gain

    poly = response.response_stages[0]
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
            temp += c * np.power(volt, i)
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
            temp += c * np.power(count, i)
        if temp >= poly.approximation_lower_bound and temp <= poly.approximation_upper_bound:
            x2.append(temp)
            y2.append(count)

    if axes:
        ax1, ax2 = axes
        fig = ax1.figure
    else:
        fig = plt.figure()
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
        fig.savefig(outfile)
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

    # We'll use the overall gain to scale between Volts and Counts
    net_gain = 1.
    for i, stage in enumerate(response.response_stages):
        if stage.stage_gain:
            net_gain *= stage.stage_gain

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
            temp += c * np.power(volt, i)
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
            temp += c * np.power(count, i)
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


def polynomial_or_polezero_response(response):
    response_str = str(response)
    if response.instrument_polynomial:
        try:
            to_return = print_polynomial_resp(response)
        except Exception:
            to_return = 'Polynomial Response is Broken'
    else:
        try:
            polezero_stage_str = response.get_sacpz()
            to_return = '\n\nPolezeroStage\n'.join([response_str, polezero_stage_str])
        except Exception as e:
            to_return = str(e)
    return to_return

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
import pickle
from random import random
from yasmine.app.helpers.etag_helper import EtagHelper
from yasmine.app.helpers.utils.utils import ChannelUtils
from yasmine.app.settings import MEDIA_ROOT
from yasmine.app.utils.response_plot import polynomial_or_polezero_response, _units_to_evalresp_output


# IRIS SI unit normalization (stationxml-seed-converter). Case-insensitive
# variants map to canonical form for consistent sensor/datalogger chaining.
_UNIT_NORMALIZE_CS = {
    # voltage -> "V"
    "V": "V",
    "v": "V",
    "Volt": "V",
    "Volts": "V",
    "VOLT": "V",
    "VOLTS": "V",
    "volt": "V",
    "volts": "V",

    # millivolt -> "mV"
    "mV": "mV",
    "mv": "mV",
    "Millivolt": "mV",
    "Millivolts": "mV",
    "MILLIVOLT": "mV",
    "MILLIVOLTS": "mV",
    "millivolt": "mV",
    "millivolts": "mV",

    # microvolt -> "uV" (ascii-совместимо)
    "uV": "uV",
    "uv": "uV",
    "µV": "uV",  # U+00B5
    "µv": "uV",
    "μV": "uV",  # U+03BC
    "μv": "uV",
    "Microvolt": "uV",
    "Microvolts": "uV",
    "MICROVOLT": "uV",
    "MICROVOLTS": "uV",
    "microvolt": "uV",
    "microvolts": "uV",

    # digital counts -> "count" (строго единичное, lower)
    "count": "count",
    "counts": "count",
    "Count": "count",
    "Counts": "count",
    "COUNT": "count",
    "COUNTS": "count",

    # length -> "m"
    "m": "m",
    "meter": "m",
    "meters": "m",
    "Meter": "m",
    "Meters": "m",
    "METER": "m",
    "METERS": "m",

    # velocity / acceleration -> "m/s", "m/s**2"
    "m/s": "m/s",
    "M/S": "m/s",
    "m/s**2": "m/s**2",
    "M/S**2": "m/s**2",
    "m/s2": "m/s**2",
    "M/S2": "m/s**2",
    "m/s^2": "m/s**2",
    "M/S^2": "m/s**2",
    "m/s/s": "m/s**2",
    "M/S/S": "m/s**2",

    # time -> "s"
    "s": "s",
    "second": "s",
    "seconds": "s",
    "Second": "s",
    "Seconds": "s",
    "SECOND": "s",
    "SECONDS": "s",

    # pressure -> "Pa"
    "Pa": "Pa",
    "pa": "Pa",
    "Pascal": "Pa",
    "Pascals": "Pa",
    "PASCAL": "Pa",
    "PASCALS": "Pa",
    "pascal": "Pa",
    "pascals": "Pa",

    # frequency -> "Hz"
    "Hz": "Hz",
    "hz": "Hz",
    "Hertz": "Hz",
    "HERTZ": "Hz",
    "hertz": "Hz",

    # angles -> "rad", "deg"
    "rad": "rad",
    "Rad": "rad",
    "RAD": "rad",
    "radian": "rad",
    "radians": "rad",
    "Radian": "rad",
    "Radians": "rad",
    "RADIAN": "rad",
    "RADIANS": "rad",

    "deg": "deg",
    "Deg": "deg",
    "DEG": "deg",
    "degree": "deg",
    "degrees": "deg",
    "Degree": "deg",
    "Degrees": "deg",
    "DEGREE": "deg",
    "DEGREES": "deg",

    # current -> "A"
    "A": "A",
    "a": "A",
    "ampere": "A",
    "amperes": "A",
    "Ampere": "A",
    "Amperes": "A",
    "AMPERE": "A",
    "AMPERES": "A",

    # force -> "N"
    "N": "N",
    "n": "N",
    "newton": "N",
    "newtons": "N",
    "Newton": "N",
    "Newtons": "N",
    "NEWTON": "N",
    "NEWTONS": "N",

    # power -> "W"
    "W": "W",
    "w": "W",
    "watt": "W",
    "watts": "W",
    "Watt": "W",
    "Watts": "W",
    "WATT": "W",
    "WATTS": "W",
}

# Case-insensitive lookup: lowercase key -> canonical value
_UNIT_NORMALIZE = {k.lower(): v for k, v in _UNIT_NORMALIZE_CS.items()}


def _normalize_unit(name):
    """Normalize unit name to SI canonical form for chain consistency."""
    if not name or not isinstance(name, str):
        return name
    s = name.strip()
    if not s:
        return name
    key = s.lower()
    return _UNIT_NORMALIZE.get(key, s)


def _get_unit_str(unit):
    """Extract unit string from ObsPy unit (can be str or object with .name)."""
    if unit is None:
        return None
    if isinstance(unit, str):
        return unit.strip() or None
    return getattr(unit, 'name', None) or getattr(unit, 'value', None) or str(unit)


def _is_ground_motion_unit(unit_str):
    """True if unit is displacement, velocity, or acceleration (m, m/s, m/s**2)."""
    return _units_to_evalresp_output(unit_str) is not None


def _normalize_response_units(response):
    """Normalize input_units/output_units in response stages and instrument_sensitivity.
    Also fills None units from neighboring stages (ObsPy NRL sets first datalogger
    stage to None; we fix after combine).
    """
    if response is None:
        return response
    stages = response.response_stages or []
    sens = getattr(response, 'instrument_sensitivity', None)
    # Pass 1: fill None from neighbors (multiple passes for chains of None)
    for _ in range(len(stages) + 1):
        changed = False
        for i, stage in enumerate(stages):
            if not _get_unit_str(stage.input_units):
                prev = _get_unit_str(stages[i - 1].output_units) if i > 0 else _get_unit_str(sens.input_units) if sens else None
                if prev:
                    stage.input_units = prev
                    changed = True
                elif i > 0 and i < len(stages) - 1:
                    # Fallback: intermediate stage between sensor and digitizer is typically V
                    stage.input_units = 'V'
                    changed = True
            if not _get_unit_str(stage.output_units):
                nxt = _get_unit_str(stages[i + 1].input_units) if i < len(stages) - 1 else _get_unit_str(sens.output_units) if sens else None
                if nxt:
                    stage.output_units = nxt
                    changed = True
                elif i > 0 and i < len(stages) - 1:
                    stage.output_units = 'V'
                    changed = True
        if not changed:
            break
    # Pass 2: normalize all (ensure strings for EVRESP compatibility)
    for stage in stages:
        iu = _get_unit_str(stage.input_units)
        if iu:
            stage.input_units = _normalize_unit(iu)
        ou = _get_unit_str(stage.output_units)
        if ou:
            stage.output_units = _normalize_unit(ou)
    if sens:
        siu = _get_unit_str(sens.input_units)
        if siu:
            sens.input_units = _normalize_unit(siu)
        sou = _get_unit_str(sens.output_units)
        if sou:
            sens.output_units = _normalize_unit(sou)
    poly = getattr(response, 'instrument_polynomial', None)
    if poly:
        piu = _get_unit_str(poly.input_units)
        if piu:
            poly.input_units = _normalize_unit(piu)
        pou = _get_unit_str(poly.output_units)
        if pou:
            poly.output_units = _normalize_unit(pou)
    # Preserve ground-motion input type on instrument_sensitivity (accel vs vel vs disp).
    if sens and stages:
        stage0_iu = _get_unit_str(stages[0].input_units)
        if _is_ground_motion_unit(stage0_iu):
            sens.input_units = stages[0].input_units
            desc = getattr(stages[0], 'input_units_description', None)
            if desc:
                sens.input_units_description = desc
    return response


class BaseHelper:
    def __init__(self, root_folder, library_url, *_, **__):
        self.root_folder = root_folder
        self.library_url = library_url
        self.etag_helper = EtagHelper(root_folder, library_url)
        self.sensor_keys_file = 'sensors.json'
        self.datalogger_keys_file = 'dataloggers.json'
        self.content_folder = os.path.join(root_folder, 'content')
        self.plot_folder = os.path.join(MEDIA_ROOT, 'plots')
        os.makedirs(self.content_folder, exist_ok=True)
        os.makedirs(self.plot_folder, exist_ok=True)

    def sync(self):
        if not self.etag_helper.is_new_etag_available():
            return
        self._load_library()
        self._create_keys_files()
        self.etag_helper.save_etag()

    def get_channel_response_obj(self, sensor_keys, datalogger_keys):
        raise NotImplementedError('Subclass needs to implement this method')

    def _load_library(self):
        raise NotImplementedError('Subclass needs to implement this method')

    def _create_keys_files(self):
        raise NotImplementedError('Subclass needs to implement this method')

    def get_sensors_keys(self):
        return self._load_keys_file(self.sensor_keys_file)

    def get_dataloggers_keys(self):
        return self._load_keys_file(self.datalogger_keys_file)

    def get_channel_response_str(self, sensor_keys, datalogger_keys):
        response = self.get_channel_response_obj(sensor_keys, datalogger_keys)
        return polynomial_or_polezero_response(response)

    def generate_channel_response_plot(self, response, sensors_keys, datalogger_keys, min_frequency,
                                       max_frequency, instconfig=None):
        file_name = ''.join(sensors_keys) + '_' + ''.join(datalogger_keys)
        return ChannelUtils.create_response_plot(
            response, self.plot_folder, file_name, min_frequency, max_frequency,
            instconfig=instconfig)

    def generate_channel_response_csv(self, response, sensors_keys, datalogger_keys, min_frequency,
                                      max_frequency, instconfig=None):
        file_name = ''.join(sensors_keys) + '_' + ''.join(datalogger_keys)
        return ChannelUtils.create_response_csv(
            response, self.plot_folder, file_name, min_frequency, max_frequency,
            instconfig=instconfig)

    def get_sensor_response_and_plot(self, sensor_keys, datalogger_keys, min_fq, max_fq):
        try:
            response_str = self.get_channel_response_str(sensor_keys, datalogger_keys)
        except Exception as err:
            return {'success': False, 'message': f'Cannot build channel response.<br> {err}'}
        try:
            resp = self.get_channel_response_obj(sensor_keys, datalogger_keys)
            min_fq = float(min_fq) if min_fq else None
            max_fq = float(max_fq) if max_fq else None
            plot_file_name = self.generate_channel_response_plot(resp, sensor_keys, datalogger_keys, min_fq, max_fq)
            plot_url = f'/api/channel/response/plots/plots/{plot_file_name}?_dc={random()}'
            csv_file_name = self.generate_channel_response_csv(resp, sensor_keys, datalogger_keys, min_fq, max_fq)
            csv_url = f'/api/channel/response/plots/plots/{csv_file_name}?_dc={random()}'
        except Exception as err:
            import logging
            import traceback
            logging.getLogger(__name__).exception('Cannot generate plot')
            err_str = str(err).lower()
            if 'units mismatch' in err_str or 'check_channel' in err_str or 'illegal resp format' in err_str:
                msg = (
                    'Cannot generate plot: units mismatch between sensor and datalogger stages. '
                    'This may indicate an incompatible combination in the NRL. '
                    '<b>The response data is available below and can still be added.</b>'
                )
            else:
                tb_lines = traceback.format_exc().strip().split('\n')[-5:]
                msg = f'Cannot generate plot.<br>{err}<br><small>{"<br>".join(tb_lines)}</small>'
            return {'success': True, 'text': response_str, 'message': msg, 'plot_failed': True}

        return {'success': True, 'text': response_str, 'plot_url': plot_url, 'csv_url': csv_url}

    def _save_keys_files(self, sensors, dataloggers):
        with open(os.path.join(self.root_folder, self.sensor_keys_file), 'wb') as outfile:
            outfile.write(pickle.dumps(sensors))
        with open(os.path.join(self.root_folder, self.datalogger_keys_file), 'wb') as outfile:
            outfile.write(pickle.dumps(dataloggers))

    def _load_keys_file(self, key_file_name):
        file = os.path.join(self.root_folder, key_file_name)
        if not os.path.exists(file):
            return [{'text': 'Library is not loaded yet...'}]
        with open(file, 'rb') as outfile:
            return pickle.loads(outfile.read())

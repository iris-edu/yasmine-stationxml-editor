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
# 2026-09-29, version 4.4.0-beta: ASGSR, Alexey Emanov
#
# ****************************************************************************/


from yasmine.app.helpers.nrl.seed_channel_prefix import suggest_channel_prefix


class IalChannelCodeHelper:
    """SEED channel suggest for AROL (IAL) sensor + datalogger dicts."""

    def guess_code(self, sensor_response, datalogger_response):
        sample_rate = self._sample_rate(datalogger_response) or self._sample_rate(sensor_response)
        input_units = self._input_units(sensor_response)
        description = self._description(sensor_response)
        angular_period = self._angular_period(sensor_response)
        suggestion = suggest_channel_prefix(
            sensor_type=None,
            angular_period=angular_period,
            sample_rate=sample_rate,
            input_units=input_units,
            description=description,
        )
        prefix = suggestion.get('prefix') or ''
        band = suggestion.get('band') or ''
        # Match NRL helper return: (instrument/channel stem, band letter).
        stem = suggestion.get('code') or prefix
        if stem and band and stem.startswith(band):
            stem = stem[len(band):]
        return stem or '', band or ''

    @staticmethod
    def _sample_rate(response_dict):
        if not isinstance(response_dict, dict):
            return None
        stages = ((response_dict.get('response') or {}).get('stages')) or []
        for stage in reversed(list(stages)):
            rate = stage.get('decimation_input_sample_rate')
            factor = stage.get('decimation_factor')
            try:
                if rate is not None and factor not in (None, 0, '0'):
                    return float(rate) / float(factor)
                if rate is not None:
                    return float(rate)
            except (TypeError, ValueError, ZeroDivisionError):
                continue
            for key in ('sample_rate', 'output_sample_rate', 'input_sample_rate'):
                try:
                    if stage.get(key) is not None:
                        return float(stage.get(key))
                except (TypeError, ValueError):
                    continue
        return None

    @staticmethod
    def _input_units(response_dict):
        if not isinstance(response_dict, dict):
            return None
        stages = ((response_dict.get('response') or {}).get('stages')) or []
        if not stages:
            return None
        units = stages[0].get('input_units')
        if isinstance(units, dict):
            return units.get('name')
        return units

    @staticmethod
    def _description(response_dict):
        if not isinstance(response_dict, dict):
            return ''
        for key in ('description', 'model', 'name', 'type'):
            value = response_dict.get(key)
            if value:
                return str(value)
        return ''

    @staticmethod
    def _angular_period(response_dict):
        if not isinstance(response_dict, dict):
            return None
        stages = ((response_dict.get('response') or {}).get('stages')) or []
        for stage in stages:
            filt = stage.get('filter') or {}
            if isinstance(filt, dict):
                for key in ('normalization_frequency', 'stage_gain_frequency'):
                    try:
                        freq = float(filt.get(key) or stage.get(key))
                    except (TypeError, ValueError):
                        freq = None
                    if freq and freq > 0:
                        return 1.0 / freq
            try:
                freq = float(stage.get('normalization_frequency') or stage.get('stage_gain_frequency'))
            except (TypeError, ValueError):
                freq = None
            if freq and freq > 0:
                return 1.0 / freq
        return None

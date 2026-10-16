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
# 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
#
# ****************************************************************************/


from yasmine.app.enums.library import LibraryTypeEnum
from yasmine.app.exceptions.exceptions import BusinessException
from yasmine.app.enums.xml_node import XmlNodeAttrEnum
from yasmine.app.handlers.base import AsyncThreadMixin, BaseHandler
from yasmine.app.handlers.equipment import EquipmentMixin
from yasmine.app.helpers.library_helper_factory import LibraryHelperFactory
from yasmine.app.helpers.nrl.seed_channel_prefix import (
    angular_period_from_keys,
    angular_period_from_low_frequency_corner,
    input_units_from_text,
    motion_is_clear,
    parse_number,
    response_sample_rate_and_units,
    sample_rate_from_keys,
    suggest_channel_prefix,
    units_and_legacy_from_resp,
)
from yasmine.app.helpers.nrl.soh_channel_code import (
    description_from_keys,
    description_from_units,
    parse_sample_rate,
    parse_soh_resp,
    suggest_soh_code,
)
from yasmine.app.services.wizard_service import WizardService


class CreateGuessCodeHandler(AsyncThreadMixin, BaseHandler):
    def async_post(self, *_, **__):
        params = self.request_params
        sensor_keys = params.get('sensorKeys')
        datalogger_keys = params.get('dataloggerKeys')
        library_type = params.get('libraryType')
        try:
            helper = LibraryHelperFactory().get_helper(library_type)
            chan_code, _ = helper.guess_channel_code(sensor_keys, datalogger_keys)
        except (ValueError, KeyError, TypeError, IndexError, AttributeError, OSError):
            return ''
        return chan_code or ''


class GuessSohCodeHandler(AsyncThreadMixin, BaseHandler):
    def async_post(self, *_, **__):
        params = self.request_params
        description = params.get('channelDescription') or None
        sample_rate = params.get('sampleRate')
        keys = params.get('sensorKeys') or []
        library_type = params.get('libraryType')
        if library_type == LibraryTypeEnum.NRL and keys and not description:
            try:
                helper = LibraryHelperFactory().get_helper(library_type)
                text = helper.get_element_response_str('soh', keys)
                units, rate = parse_soh_resp(text)
                description = description_from_keys(keys) or description_from_units(units)
                if sample_rate in (None, ''):
                    sample_rate = rate
            except Exception:
                pass
        suggestion = suggest_soh_code(description, sample_rate)
        suggestion['sampleRate'] = parse_sample_rate(sample_rate)
        return suggestion


class GuessChannelPrefixHandler(AsyncThreadMixin, BaseHandler):
    def async_post(self, *_, **__):
        params = self.request_params
        sensor_type = params.get('sensorType') or None
        angular_period = params.get('angularPeriod')
        sample_rate = params.get('sampleRate')
        input_units = params.get('inputUnits') or None
        description = params.get('description') or ''
        legacy = params.get('legacyInstrument') or None
        sensor_keys = params.get('sensorKeys') or []
        datalogger_keys = params.get('dataloggerKeys') or []
        library_type = params.get('libraryType')
        response_type = params.get('nrlResponseType')

        if library_type == LibraryTypeEnum.NRL and response_type != 'soh':
            # Offline NRL has no sensor-type field. Read the combined
            # response and treat the sensor as broadband.
            rate, units = self._nrl_offline_response_facts(
                response_type, sensor_keys, datalogger_keys
            )
            if rate not in (None, ''):
                sample_rate = rate
            if units:
                input_units = units
            # Ignore a caller-supplied period. Offline NRL states the corner
            # in the sensor keys (120 s, 4.5 Hz), not in a separate type field.
            angular_period = None
            sensor_type = None
            legacy = None
            description = ''
        if not description:
            description = ' '.join(str(key) for key in list(sensor_keys) + list(datalogger_keys))
        if angular_period in (None, '') and library_type == LibraryTypeEnum.NRLV2_ONLINE:
            angular_period = angular_period_from_low_frequency_corner(description)
        if angular_period in (None, ''):
            angular_period = angular_period_from_keys(sensor_keys)
            if angular_period in (None, '') and library_type == LibraryTypeEnum.NRL:
                angular_period = angular_period_from_low_frequency_corner(description)
        if sample_rate in (None, ''):
            sample_rate = sample_rate_from_keys(sensor_keys, datalogger_keys)
        if not motion_is_clear(sensor_type) and not input_units:
            input_units, resp_legacy = self._units_from_library(
                library_type, response_type, sensor_keys, datalogger_keys,
                params.get('instconfig'), params.get('inputUnitsText'),
            )
            if not legacy:
                legacy = resp_legacy
        suggestion = suggest_channel_prefix(
            sensor_type=sensor_type,
            angular_period=angular_period,
            sample_rate=sample_rate,
            input_units=input_units,
            description=description,
            legacy_instrument=legacy,
        )
        suggestion['sampleRate'] = parse_number(sample_rate)
        return suggestion

    def _nrl_offline_response_facts(self, response_type, sensor_keys, datalogger_keys):
        """Sample rate and input units of the NRL Offline channel response."""
        try:
            helper = LibraryHelperFactory().get_helper(LibraryTypeEnum.NRL)
            if response_type == 'integrated':
                keys = sensor_keys or datalogger_keys
                if not keys:
                    return None, None
                response = helper.get_element_response_obj('integrated', keys)
            elif sensor_keys and datalogger_keys:
                response = helper.get_channel_response_obj(sensor_keys, datalogger_keys)
            else:
                return None, None
        except Exception:
            return None, None
        return response_sample_rate_and_units(response)

    def _units_from_library(self, library_type, response_type, sensor_keys,
                            datalogger_keys, instconfig, preview_text):
        """Input units for a sensor or integrated response whose type is unclear."""
        if response_type == 'soh':
            return None, None
        parsed = input_units_from_text(preview_text)
        if parsed:
            return parsed, None
        try:
            if library_type == LibraryTypeEnum.NRLV2_ONLINE and instconfig:
                helper = LibraryHelperFactory().get_helper(
                    library_type, application=getattr(self, 'application', None)
                )
                response = helper.get_channel_response_obj(instconfig)
                stages = getattr(response, 'response_stages', None) or []
                if stages and stages[0].input_units:
                    return str(stages[0].input_units), None
                return None, None
            if library_type not in (LibraryTypeEnum.NRL, LibraryTypeEnum.AROL):
                return None, None
            helper = LibraryHelperFactory().get_helper(library_type)
            if response_type == 'integrated':
                text = helper.get_element_response_str(
                    'integrated', sensor_keys or datalogger_keys
                )
            elif sensor_keys:
                text = helper.get_sensor_response_str(sensor_keys)
            else:
                return None, None
        except Exception:
            return None, None
        units, legacy = units_and_legacy_from_resp(text)
        if not units:
            units = input_units_from_text(text)
        return units, legacy


class CreateNetworkHandler(AsyncThreadMixin, BaseHandler):
    def async_post(self, **__):
        params = self.request_params
        try:
            network_id = WizardService(self).create_network(
                xml_id=params.get('xmlId'),
                code=params.get(XmlNodeAttrEnum.CODE),
                start_date=params.get(XmlNodeAttrEnum.START_DATE),
                end_date=params.get(XmlNodeAttrEnum.END_DATE),
            )
        except BusinessException as err:
            return {'success': False, 'message': str(err)}
        return {'success': True, 'network_id': network_id}


class CreateStationHandler(AsyncThreadMixin, BaseHandler):
    def async_post(self, **__):
        params = self.request_params
        try:
            station_id = WizardService(self).create_station(
                xml_id=params.get('xmlId'),
                code=params.get(XmlNodeAttrEnum.CODE),
                start_date=params.get(XmlNodeAttrEnum.START_DATE),
                end_date=params.get(XmlNodeAttrEnum.END_DATE),
                network_id=params.get('networkNodeId'),
                latitude=params.get(XmlNodeAttrEnum.LATITUDE),
                longitude=params.get(XmlNodeAttrEnum.LONGITUDE),
                elevation=params.get(XmlNodeAttrEnum.ELEVATION),
            )
        except BusinessException as err:
            return {'success': False, 'message': str(err)}
        return {'success': True, 'station_id': station_id}

    def async_get(self, network_node_id=None, **__):
        data = WizardService(self).get_station_info(network_node_id)
        return {'data': data}


class CreateChannelHandler(AsyncThreadMixin, EquipmentMixin, BaseHandler):
    def async_post(self, **__):
        params = self.request_params
        try:
            channel_ids = WizardService(self).create_channels(
                xml_id=params.get('xmlId'),
                code_list=list(filter(None, [params.get('code1'), params.get('code2'), params.get('code3')])),
                start_date=params.get(XmlNodeAttrEnum.START_DATE),
                end_date=params.get(XmlNodeAttrEnum.END_DATE),
                station_id=params.get('stationNodeId'),
                dip_list=[params.get('dip1'), params.get('dip2'), params.get('dip3')],
                azimuth_list=[params.get('azimuth1'), params.get('azimuth2'), params.get('azimuth3')],
                latitude=params.get(XmlNodeAttrEnum.LATITUDE),
                longitude=params.get(XmlNodeAttrEnum.LONGITUDE),
                elevation=params.get(XmlNodeAttrEnum.ELEVATION),
                location_code=params.get(XmlNodeAttrEnum.LOCATION_CODE),
                depth=params.get(XmlNodeAttrEnum.DEPTH),
                omit_dip_azimuth=bool(params.get('omitDipAzimuth')),
                sample_rate=params.get('sampleRate'),
                library_type=params.get('libraryType'),
                sensor_keys=params.get('sensorKeys') or params.get('instconfig'),
                datalogger_keys=params.get('dataloggerKeys'),
                response_tree=params.get('responseTree'),
                nrl_response_type=params.get('nrlResponseType'),
                nrlv2_source=params.get('source'),
            )
        except BusinessException as err:
            return {'success': False, 'message': str(err), 'channel_ids': []}
        return {'success': True, 'channel_ids': channel_ids}

    def async_get(self, station_node_id, **__):
        data = WizardService(self).get_channel_info(station_node_id)
        return {'data': data}

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
# 2026-09-24, version 4.3.3-beta: ASGSR, Alexey Emanov
#
# ****************************************************************************/


import io
import os
from contextlib import redirect_stderr
from random import random

from yasmine.app.enums.xml_node import XmlNodeAttrEnum
from yasmine.app.handlers.base import AsyncThreadMixin, BaseHandler
from yasmine.app.helpers.utils.utils import (
    ChannelUtils,
    plot_max_frequency,
    response_plot_stages,
)
from yasmine.app.models import XmlNodeInstModel
from yasmine.app.settings import MEDIA_ROOT
from yasmine.app.utils.imp_exp import ConvertToInventory
from yasmine.app.utils.response_plot import (
    format_plot_failure,
    format_sensitivity_failure,
    polynomial_or_polezero_response,
)
from yasmine.app.utils.resp_import import import_resp_into_channel
from yasmine.app.utils.response_sensitivity import (
    PolynomialResponseError,
    get_sensitivity_recalculate_options,
    load_response_from_preview_params,
    preview_plot_basename,
    recalculate_response_sensitivity,
    response_obj_to_tree_json,
    response_obj_to_tree_json_standalone,
)
from yasmine.app.utils.response_schema import (
    get_response_descriptor,
    response_descriptor_etag,
    validate_response_tree,
)
from yasmine.app.utils.response_tree import station_xml_response_to_tree


class XmlChannelResponsePlotHandler(AsyncThreadMixin, BaseHandler):
    def async_get(self, *_, **__):
        node_id = self.get_argument('nodeInstanceId')
        try:
            channel = ConvertToInventory(None, self).convert_channel(node_id)
        except (ValueError, KeyError, TypeError) as err:
            return {'success': False, 'message': str(err)}
        plot_folder = os.path.join(MEDIA_ROOT, 'plots')
        min_fq = self.get_argument('min')
        max_fq = self.get_argument('max')
        start_stage = self.get_argument('start_stage', None)
        end_stage = self.get_argument('end_stage', None)

        try:
            with redirect_stderr(io.StringIO()):
                stage_tag = ''
                if start_stage not in (None, ''):
                    stage_tag += f'_s{start_stage}'
                if end_stage not in (None, ''):
                    stage_tag += f'_e{end_stage}'
                plot_basename = f'channel_node_{node_id}{stage_tag}'
                plot_file = ChannelUtils.create_response_plot(
                    channel.response,
                    plot_folder,
                    plot_basename,
                    float(min_fq) if min_fq else None,
                    float(max_fq) if max_fq else None,
                    start_stage=start_stage,
                    end_stage=end_stage,
                )
                plot_csv = ChannelUtils.create_response_csv(
                    channel.response,
                    plot_folder,
                    plot_basename,
                    float(min_fq) if min_fq else None,
                    float(max_fq) if max_fq else None,
                    start_stage=start_stage,
                    end_stage=end_stage,
                )
        except ValueError as err:
            return {'success': False, 'message': str(err)}
        except Exception as err:
            return {'success': False, 'message': format_plot_failure(err, channel.response)}

        return {
            'success': True,
            'plot_url': f'/api/channel/response/plots/plots/{plot_file}?_dc={random()}',
            'csv_url': f'/api/channel/response/plots/plots/{plot_csv}?_dc={random()}',
            'max_frequency': plot_max_frequency(
                channel.response,
                float(max_fq) if max_fq else None,
                float(min_fq) if min_fq else None,
            ),
            'stages': response_plot_stages(channel.response),
        }


class XmlChannelResponseDifferencePlotHandler(AsyncThreadMixin, BaseHandler):
    def async_get(self, *_, **__):
        node1_id = int(self.get_argument('nodeInstance1Id'))
        node2_id = int(self.get_argument('nodeInstance2Id'))
        max = self.get_argument('max')
        min = self.get_argument('min')

        response1 = None
        channel1 = self.db.query(XmlNodeInstModel).filter(XmlNodeInstModel.id == node1_id).first()
        if channel1 is None:
            return {'success': False, 'message': 'Channel 1 not found'}
        for chn1_attr_val in channel1.attr_vals:
            if chn1_attr_val.attr.name == XmlNodeAttrEnum.RESPONSE:
                response1 = chn1_attr_val.value_obj

        response2 = None
        channel2 = self.db.query(XmlNodeInstModel).filter(XmlNodeInstModel.id == node2_id).first()
        if channel2 is None:
            return {'success': False, 'message': 'Channel 2 not found'}
        for chn2_attr_val in channel2.attr_vals:
            if chn2_attr_val.attr.name == XmlNodeAttrEnum.RESPONSE:
                response2 = chn2_attr_val.value_obj

        try:
            with redirect_stderr(io.StringIO()):
                plot_folder = os.path.join(MEDIA_ROOT, 'plots')
                name = f'response_diff_{node1_id}_{node2_id}'
                file = ChannelUtils.create_response_plot_difference(
                    response1,
                    response2,
                    plot_folder,
                    name,
                    float(min) if min else None,
                    float(max) if max else None)
        except Exception as err:
            return {'success': False, 'message': f'Cannot generate plot.<br> {err}'}

        return {'success': True, 'message': f'/api/channel/response/plots/plots/{file}?_dc={random()}'}


class XmlChannelResponseXmlHandler(AsyncThreadMixin, BaseHandler):
    def async_get(self, *_, **__):
        node_id = self.get_argument('nodeInstanceId')

        try:
            station_xml = ConvertToInventory(None, self).get_station_xml_for_channel(node_id)
            channel_response = station_xml_response_to_tree(station_xml)
        except Exception as err:
            return {'success': False, 'message': f'Cannot generate xml channel response.<br> {err}'}

        return {'success': True, 'data': channel_response}


class XmlChannelResponseSchemaHandler(AsyncThreadMixin, BaseHandler):
    """GET the cached StationXML 1.2 Response editor descriptor."""

    def async_get(self, *_, **__):
        self.set_header('Cache-Control', 'public, max-age=86400, immutable')
        self.set_header('ETag', '"%s"' % response_descriptor_etag())
        return {
            'success': True,
            'data': get_response_descriptor(),
        }


class XmlChannelResponseValidateHandler(AsyncThreadMixin, BaseHandler):
    """POST legacy response tree JSON and return XSD errors plus operational warnings."""

    def async_post(self, *_, **__):
        params = self.request_params
        payload = params.get('response', params) if isinstance(params, dict) else params
        issues = validate_response_tree(payload)
        valid = not any(issue['severity'] == 'error' for issue in issues)
        return {
            'success': True,
            'valid': valid,
            'issues': issues,
            'data': issues,
        }


def _recalculate_identity_error(params):
    node_inst_id = params.get('nodeInstanceId')
    instconfig = params.get('instconfig')
    library_type = params.get('libraryType')
    sensor_keys = params.get('sensorKeys')
    datalogger_keys = params.get('dataloggerKeys')
    if not node_inst_id and not instconfig and not (
            library_type and sensor_keys and datalogger_keys):
        return {
            'success': False,
            'message': 'nodeInstanceId, instconfig, or libraryType with sensorKeys and dataloggerKeys required',
        }
    return None


def _recalculate_kwargs_from_params(params):
    """Parse frequencyMode/frequency for recalculate_response_sensitivity."""
    kwargs = {}
    allow = params.get('allowZeroGainReset')
    if allow in (True, 'true', 'True', '1', 1):
        kwargs['allow_zero_gain_reset'] = True
    mode = params.get('frequencyMode')
    if mode == 'auto':
        kwargs['auto'] = True
        return kwargs
    if mode == 'custom':
        raw = params.get('frequency')
        if raw is None or raw == '':
            raise ValueError('frequency is required when frequencyMode is custom')
        freq = float(raw)
        if freq <= 0:
            raise ValueError('frequency must be greater than zero')
        kwargs['frequency'] = freq
        return kwargs
    return kwargs


class XmlChannelResponseRecalculateSensitivityOptionsHandler(AsyncThreadMixin, BaseHandler):
    """POST /api/channel/response/recalculate-sensitivity-options/ - Dialog values."""

    def async_post(self, *_, **__):
        params = self.request_params
        identity_error = _recalculate_identity_error(params)
        if identity_error:
            return identity_error

        response = None
        try:
            with redirect_stderr(io.StringIO()):
                response = load_response_from_preview_params(params, self)
                options = get_sensitivity_recalculate_options(response)
        except PolynomialResponseError as err:
            return {'success': False, 'message': str(err)}
        except Exception as err:
            return {'success': False, 'message': format_sensitivity_failure(err, response)}

        return {'success': True, **options}


class XmlChannelResponseRecalculateSensitivityHandler(AsyncThreadMixin, BaseHandler):
    """POST /api/channel/response/recalculate-sensitivity/ - Recalculate InstrumentSensitivity."""

    def async_post(self, *_, **__):
        params = self.request_params
        identity_error = _recalculate_identity_error(params)
        if identity_error:
            return identity_error

        node_inst_id = params.get('nodeInstanceId')
        instconfig = params.get('instconfig')
        min_fq = params.get('min')
        max_fq = params.get('max')
        start_stage = params.get('start_stage')
        end_stage = params.get('end_stage')

        response = None
        try:
            recalculate_kwargs = _recalculate_kwargs_from_params(params)
            with redirect_stderr(io.StringIO()):
                response = load_response_from_preview_params(params, self)
                response, frequency = recalculate_response_sensitivity(
                    response, **recalculate_kwargs
                )
                if node_inst_id:
                    tree_data = response_obj_to_tree_json(response, node_inst_id, self)
                else:
                    tree_data = response_obj_to_tree_json_standalone(response)
                text = polynomial_or_polezero_response(response)
                plot_folder = os.path.join(MEDIA_ROOT, 'plots')
                plot_basename = preview_plot_basename(params)
                plot_file = ChannelUtils.create_response_plot(
                    response,
                    plot_folder,
                    plot_basename,
                    float(min_fq) if min_fq else None,
                    float(max_fq) if max_fq else None,
                    instconfig=instconfig,
                    start_stage=start_stage,
                    end_stage=end_stage,
                )
                plot_csv = ChannelUtils.create_response_csv(
                    response,
                    plot_folder,
                    plot_basename,
                    float(min_fq) if min_fq else None,
                    float(max_fq) if max_fq else None,
                    instconfig=instconfig,
                    start_stage=start_stage,
                    end_stage=end_stage,
                )
        except PolynomialResponseError as err:
            return {'success': False, 'message': str(err)}
        except ValueError as err:
            return {'success': False, 'message': str(err)}
        except Exception as err:
            return {'success': False, 'message': format_sensitivity_failure(err, response)}

        sensitivity_value = response.instrument_sensitivity.value
        return {
            'success': True,
            'data': tree_data,
            'text': text,
            'plot_url': f'/api/channel/response/plots/plots/{plot_file}?_dc={random()}',
            'csv_url': f'/api/channel/response/plots/plots/{plot_csv}?_dc={random()}',
            'max_frequency': plot_max_frequency(
                response,
                float(max_fq) if max_fq else None,
                float(min_fq) if min_fq else None,
            ),
            'stages': response_plot_stages(response),
            'sensitivity_value': sensitivity_value,
            'sensitivity_frequency': frequency,
        }


class XmlChannelResponseImportRespHandler(AsyncThreadMixin, BaseHandler):
    """POST /api/channel/response/import-resp/ - Load an external RESP into a channel."""

    def async_post(self, *_, **__):
        files = self.request.files.get('file')
        if not files:
            return {'success': False, 'message': 'file is required'}
        node_inst_id = self.get_argument('nodeInstanceId', '')
        if not node_inst_id:
            return {'success': False, 'message': 'nodeInstanceId is required'}
        sensor_name = self.get_argument('sensorName', None)
        datalogger_name = self.get_argument('dataloggerName', None)
        create_equipment = self.get_argument('createEquipment', '') in (
            '1', 'true', 'True', 'yes',
        )
        try:
            imported = import_resp_into_channel(
                self,
                node_inst_id,
                files[0]['body'],
                sensor_name=sensor_name,
                datalogger_name=datalogger_name,
                create_equipment=create_equipment,
            )
        except ValueError as error:
            return {'success': False, 'message': str(error)}
        except Exception as error:
            return {'success': False, 'message': str(error)}
        result = {
            'success': True,
            'id': imported.get('id'),
            'data': imported['data'],
            'text': imported['text'],
        }
        if 'sample_rate' in imported:
            result['sample_rate'] = imported['sample_rate']
        return result

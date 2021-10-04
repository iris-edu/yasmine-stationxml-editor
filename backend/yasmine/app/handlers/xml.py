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
from random import random
from xmljson import abdera

from yasmine.app.enums.xml_node import XmlNodeAttrEnum
from yasmine.app.handlers.base import AsyncThreadMixin, BaseHandler
from yasmine.app.helpers.utils.utils import ChannelUtils
from yasmine.app.models import XmlNodeInstModel
from yasmine.app.settings import MEDIA_ROOT
from yasmine.app.utils.imp_exp import ConvertToInventory


class XmlChannelResponsePlotHandler(AsyncThreadMixin, BaseHandler):
    def async_get(self, *_, **__):
        node_id = self.get_argument('nodeInstanceId')
        channel = ConvertToInventory(None, self).convert_channel(node_id)
        plot_folder = os.path.join(MEDIA_ROOT, 'plots')
        min_fq = self.get_argument('min')
        max_fq = self.get_argument('max')

        try:
            plot_file = ChannelUtils.create_response_plot(
                channel.response,
                plot_folder,
                f'channel_node_{node_id}',
                float(min_fq) if min_fq else None,
                float(max_fq) if max_fq else None
            )
            plot_csv = ChannelUtils.create_response_csv(
                channel.response,
                plot_folder,
                f'channel_node_{node_id}',
                float(min_fq) if min_fq else None,
                float(max_fq) if max_fq else None
            )
        except Exception as err:
            return {'success': False, 'message': f'Cannot generate plot.<br> {err}'}

        return {
            'success': True,
            'plot_url': f'/api/channel/response/plots/plots/{plot_file}?_dc={random()}',
            'csv_url': f'/api/channel/response/plots/plots/{plot_csv}?_dc={random()}'
        }


class XmlChannelResponseDifferencePlotHandler(AsyncThreadMixin, BaseHandler):
    def async_get(self, *_, **__):
        node1_id = int(self.get_argument('nodeInstance1Id'))
        node2_id = int(self.get_argument('nodeInstance2Id'))
        max = self.get_argument('max')
        min = self.get_argument('min')

        response1 = None
        channel1 = self.db.query(XmlNodeInstModel).filter(XmlNodeInstModel.id == node1_id).first()
        for chn1_attr_val in channel1.attr_vals:
            if chn1_attr_val.attr.name == XmlNodeAttrEnum.RESPONSE:
                response1 = chn1_attr_val.value_obj

        response2 = None
        channel2 = self.db.query(XmlNodeInstModel).filter(XmlNodeInstModel.id == node2_id).first()
        for chn2_attr_val in channel2.attr_vals:
            if chn2_attr_val.attr.name == XmlNodeAttrEnum.RESPONSE:
                response2 = chn2_attr_val.value_obj

        try:
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
            resp_start = station_xml.find('<Response>')
            resp_end = station_xml.find('</Response>') + 11
            response_xml = station_xml[resp_start:resp_end]
            from lxml.etree import fromstring
            channel_response = abdera.data(fromstring(response_xml))
        except Exception as err:
            return {'success': False, 'message': f'Cannot generate xml channel response.<br> {err}'}

        return {'success': True, 'data': channel_response}

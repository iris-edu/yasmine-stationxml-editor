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


from yasmine.app.enums.xml_node import XmlNodeAttrEnum
from yasmine.app.handlers.base import AsyncThreadMixin, BaseHandler
from yasmine.app.handlers.equipment import EquipmentMixin
from yasmine.app.helpers.library_helper_factory import LibraryHelperFactory
from yasmine.app.services.wizard_service import WizardService


class CreateGuessCodeHandler(AsyncThreadMixin, BaseHandler):
    def async_post(self, *_, **__):
        params = self.request_params
        sensor_keys = params.get('sensorKeys')
        datalogger_keys = params.get('dataloggerKeys')
        library_type = params.get('libraryType')
        helper = LibraryHelperFactory().get_helper(library_type)
        chan_code, _ = helper.guess_channel_code(sensor_keys, datalogger_keys)
        return chan_code


class CreateNetworkHandler(AsyncThreadMixin, BaseHandler):
    def async_post(self, **__):
        params = self.request_params
        network_id = WizardService(self).create_network(
            xml_id=params.get('xmlId'),
            code=params.get(XmlNodeAttrEnum.CODE),
            start_date=params.get(XmlNodeAttrEnum.START_DATE),
            end_date=params.get(XmlNodeAttrEnum.END_DATE),
        )
        return {'success': True, 'network_id': network_id}


class CreateStationHandler(AsyncThreadMixin, BaseHandler):
    def async_post(self, **__):
        params = self.request_params
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
        return {'success': True, 'station_id': station_id}


class CreateChannelHandler(AsyncThreadMixin, EquipmentMixin, BaseHandler):
    def async_post(self, **__):
        params = self.request_params
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
            library_type=params.get('libraryType'),
            sensor_keys=params.get('sensorKeys'),
            datalogger_keys=params.get('dataloggerKeys')
        )
        return {'success': True, 'channel_ids': channel_ids}

    def async_get(self, station_node_id, **__):
        return WizardService(self).get_channel_info(station_node_id)

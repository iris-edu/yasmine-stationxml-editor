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


from _collections import OrderedDict
from builtins import Exception
from itertools import groupby
import io
import traceback
import datetime

from obspy import UTCDateTime
from obspy.core.inventory.channel import Channel
from obspy.core.inventory.network import Network
from obspy.core.inventory.station import Station
from obspy.core.inventory.inventory import read_inventory, Inventory
from obspy.core.inventory.util import Site
from slugify import slugify
from sqlalchemy.orm import joinedload
from tornado.web import HTTPError

from yasmine.app.enums.xml_node import XmlNodeEnum
from yasmine.app.models.inventory import XmlModel, XmlNodeInstModel, XmlNodeAttrRelationModel, XmlNodeAttrValModel
from yasmine.app.utils.facade import HandlerMixin


class ImportStationXml(HandlerMixin):
    def __init__(self, name, file_obj, *_, **__):
        self.file_obj = file_obj
        self.name = name
        super(ImportStationXml, self).__init__(*_, **__)

    def instantiate_node(self, data, node_id, attrs):

        inst_node = XmlNodeInstModel(node_id=node_id,
                                     code=data.code,
                                     start_date=data.start_date.datetime if data.start_date else None,
                                     end_date=data.end_date.datetime if data.end_date else None)
        for attr in attrs:
            if hasattr(data, attr.name):
                value = getattr(data, attr.name)
                if value is not None:
                    inst_node.attr_vals.append(XmlNodeAttrValModel(attr=attr,
                                                                   node_inst=inst_node,
                                                                   value_obj=getattr(data, attr.name))
                                               )
        return inst_node

    def run(self):
        inv = read_inventory(self.file_obj)
        xml = XmlModel(name=self.name, source=inv.source, sender=inv.sender, module=inv.module, uri=inv.module_uri, created_at=inv.created.datetime)
        all_attrs = self.db.query(XmlNodeAttrRelationModel).options(joinedload(XmlNodeAttrRelationModel.attr)).all()
        all_attrs.sort(key=lambda x: x.node_id, reverse=False)
        attrs_by_node_id = OrderedDict((k, [o.attr for o in list(v)]) for k, v in groupby(all_attrs, lambda r: r.node_id))
        for network in inv.networks:
            network_inst_node = self.instantiate_node(network, XmlNodeEnum.NETWORK, attrs_by_node_id[XmlNodeEnum.NETWORK])
            xml.nodes.append(network_inst_node)

            for station in network.stations:
                station_inst_node = self.instantiate_node(station, XmlNodeEnum.STATION, attrs_by_node_id[XmlNodeEnum.STATION])
                xml.nodes.append(station_inst_node)

                network_inst_node.children.append(station_inst_node)

                for channel in station.channels:
                    channel_inst_node = self.instantiate_node(channel, XmlNodeEnum.CHANNEL, attrs_by_node_id[XmlNodeEnum.CHANNEL])
                    xml.nodes.append(channel_inst_node)

                    station_inst_node.children.append(channel_inst_node)

        with self.db.begin():
            self.db.add(xml)

        return xml


class ConvertToInventory(HandlerMixin):

    def __init__(self, xml_model_id, *_, **__):
        self.xml_model_id = xml_model_id
        super(ConvertToInventory, self).__init__(*_, **__)

    def instantiate_node(self, clazz, attr_vals, params={}):
        node_atts = {}
        for attr_val in attr_vals:
            node_atts[attr_val.attr.name] = attr_val.value_obj
        node_atts.update(params)
        try:
            return clazz(**node_atts)
        except Exception as e:
            traceback.print_exc()
            raise HTTPError(reason="Unable to instantiate %s (%s): %s" % (clazz.__name__, node_atts, str(e)))

    def run(self):

        xml = self.db.query(XmlModel).get(self.xml_model_id)

        all_attrs = self.db.query(XmlNodeAttrValModel)\
            .join(XmlNodeAttrValModel.node_inst)\
            .options(joinedload(XmlNodeAttrValModel.attr))\
            .filter(XmlNodeInstModel.xml_id == self.xml_model_id)\
            .order_by(XmlNodeAttrValModel.node_inst_id)\
            .all()

        attrs_by_node_inst_id = OrderedDict((k, list(v)) for k, v in groupby(all_attrs, lambda r: r.node_inst_id))
        node_instances = xml.nodes.order_by(XmlNodeInstModel.parent_id).all()
        node_inst_by_parent_id = OrderedDict((k, list(v)) for k, v in groupby(node_instances, lambda r: r.parent_id))
        networks = []
        if None in node_inst_by_parent_id:
            for network_node in node_inst_by_parent_id[None]:
                network_attrs = attrs_by_node_inst_id[network_node.id]
                stations = []
                for station_node in node_inst_by_parent_id.get(network_node.id, []):
                    station_attrs = attrs_by_node_inst_id[station_node.id]
                    channels = []
                    for channel_node in node_inst_by_parent_id.get(station_node.id, []):
                        channel_attrs = attrs_by_node_inst_id[channel_node.id]
                        channels.append(self.instantiate_node(Channel, channel_attrs))
                    stations.append(self.instantiate_node(Station, station_attrs, {'channels': channels}))
                networks.append(self.instantiate_node(Network, network_attrs, {'stations': stations}))

        return Inventory(networks, xml.source, xml.sender, UTCDateTime(xml.created_at), xml.module, xml.uri)

    def convert_channel(self, node_inst_id):
        all_attrs = self.db.query(XmlNodeAttrValModel)\
            .filter(XmlNodeAttrValModel.node_inst_id == node_inst_id)\
            .all()

        attrs_by_node_inst_id = OrderedDict((k, list(v)) for k, v in groupby(all_attrs, lambda r: r.node_inst_id))
        channel_attrs = attrs_by_node_inst_id[int(node_inst_id)]
        return self.instantiate_node(Channel, channel_attrs)

    def get_station_xml_for_channel(self, node_inst_id):
        inv = self.get_inventory_for_channel(node_inst_id)
        output = io.BytesIO()
        inv.write(output, format="STATIONXML")
        station_xml = output.getvalue().decode('utf-8')
        output.close()

        return station_xml

    def get_inventory_for_channel(self, node_inst_id):
        channel_node = self.db.query(XmlNodeInstModel) \
            .filter(XmlNodeInstModel.id == node_inst_id) \
            .first()

        if channel_node.parent_id:
            station_node = self.db.query(XmlNodeInstModel) \
                .filter(XmlNodeInstModel.id == channel_node.parent_id) \
                .first()

        channel = self.convert_channel(node_inst_id)

        if 'station_node' in locals():
            network_node = self.db.query(XmlNodeInstModel) \
                .filter(XmlNodeInstModel.id == station_node.parent_id) \
                .first()

            station_node_attrs = self.db.query(XmlNodeAttrValModel)\
                .filter(XmlNodeAttrValModel.node_inst_id == station_node.id) \
                .all()

            station = self.instantiate_node(Station, station_node_attrs, {'channels': [channel]})
        else:
            station_attrs = {
                'code': 'MOCK_STATION',
                'creation_date': datetime.datetime.today(),
                'site': Site(name='MOCK_SITE'),
                'latitude': channel.latitude,
                'longitude': channel.longitude,
                'elevation': 60,
                'channels': [channel]
            }
            station = Station(**station_attrs)

        if 'network_node' in locals():
            network_node_attrs = self.db.query(XmlNodeAttrValModel) \
                .filter(XmlNodeAttrValModel.node_inst_id == network_node.id) \
                .all()
            network = self.instantiate_node(Network, network_node_attrs, {'stations': [station]})
        else:
            network_attrs = {
                'code': 'MOCK_NETWORK',
                'stations': [station]
            }
            network = Network(**network_attrs)

        inv_attrs = {
            'source': 'temp',
            'networks': [network]
        }
        return Inventory(**inv_attrs)


class ExportStationXml(HandlerMixin):
    def __init__(self, xml_model_id, *_, **__):
        self.xml_model_id = xml_model_id
        super(ExportStationXml, self).__init__(*_, **__)

    def run(self):
        try:
            inv = ConvertToInventory(self.xml_model_id, self).run()
        except Exception as e:
            raise HTTPError(reason="Unable to build XML: '%s'" % str(e))

        xml = self.db.query(XmlModel).get(self.xml_model_id)
        output = io.BytesIO()
        inv.write(output, format="STATIONXML")

        return "%s.xml" % slugify(xml.name), output

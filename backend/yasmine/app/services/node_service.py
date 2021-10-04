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

from datetime import datetime
from _collections import OrderedDict
from obspy import UTCDateTime
from obspy.core.inventory import Longitude, Latitude, Site, Distance
from sqlalchemy.orm import joinedload, aliased
from sqlalchemy.sql.expression import or_
from yasmine.app.enums.xml_node import XmlNodeAttrEnum, XmlNodeAttrWindetsEnum, XmlNodeEnum
from yasmine.app.models import XmlNodeInstModel, XmlModel, XmlNodeAttrModel, XmlNodeAttrValModel, UserLibraryModel
from yasmine.app.settings import DATE_FORMAT_SYSTEM
from yasmine.app.utils.facade import HandlerMixin
from yasmine.app.utils.date import strptime
from sqlalchemy import func
from itertools import groupby


class NodeService(HandlerMixin):
    def delete_node_from_xml(self, xml_id, node_id):
        with self.db.begin():
            self.db.query(XmlNodeInstModel) \
                .filter(XmlNodeInstModel.xml_id == xml_id,
                        XmlNodeInstModel.id == node_id) \
                .delete()
            self._update_xml_datetime(xml_id)

    def delete_node_from_library(self, library_id, node_type, node_inst_id):
        with self.db.begin():
            self.db.query(XmlNodeInstModel) \
                .filter(XmlNodeInstModel.user_library_id == library_id,
                        XmlNodeInstModel.id == node_inst_id,
                        XmlNodeInstModel.node_id == node_type) \
                .delete()
            self._update_library_datetime(library_id)

    def create_default_node_for_xml(self, xml_id, node_type, parent_id):
        with self.db.begin():
            parent = self.db.query(XmlNodeInstModel).get(parent_id) if parent_id else None
            utc_now = datetime.utcnow().replace(microsecond=0)
            node = self._create_default_node_for_xml(xml_id, node_type, parent, utc_now)
            self.db.add(node)
            self._update_xml_datetime(xml_id)
        return node.id

    def create_default_node_for_library(self, library_id, node_type, parent_id):
        with self.db.begin():
            parent = self.db.query(XmlNodeInstModel).get(parent_id) if parent_id else None
            node = self._create_default_node_for_library(node_type, library_id, parent)
            self.db.add(node)
            self._update_library_datetime(library_id)
        return node.id

    def add_node_to_library(self, library_id, node_id):
        with self.db.begin():
            node_to_clone = self.db.query(XmlNodeInstModel).get(node_id)
            utc_now = datetime.utcnow().replace(microsecond=0)
            new_node = self._clone_node_and_active_children(node_to_clone, utc_now, None, None, library_id)
            self.db.add(new_node)
            self._update_library_datetime(library_id)
        return new_node.id

    def add_node_to_xml(self, xml_id, node_id, parent_id):
        with self.db.begin():
            node_to_clone = self.db.query(XmlNodeInstModel).get(node_id)
            parent = self.db.query(XmlNodeInstModel).get(parent_id) if parent_id else None
            utc_now = datetime.utcnow().replace(microsecond=0)
            new_node = self._clone_node_and_active_children(node_to_clone, utc_now, xml_id, parent, None)
            self.db.add(new_node)
            self._update_xml_datetime(xml_id)
        return new_node.id

    def load_node_from_xml(self, xml_id, parent_id, filters):
        if parent_id == '0':
            nodes = self.db.query(XmlNodeInstModel) \
                .join(XmlNodeInstModel.node) \
                .options(joinedload(XmlNodeInstModel.node)) \
                .filter(XmlNodeInstModel.xml_id == xml_id) \
                .filter(XmlNodeInstModel.parent_id.is_(None))
        else:
            parent = self.db.query(XmlNodeInstModel).get(int(parent_id))
            parent_name = aliased(XmlNodeInstModel)
            nodes = self.db.query(XmlNodeInstModel) \
                .join(XmlNodeInstModel.node) \
                .join(parent_name, XmlNodeInstModel.parent) \
                .options(joinedload(XmlNodeInstModel.node)) \
                .options(joinedload(XmlNodeInstModel.parent)) \
                .filter(XmlNodeInstModel.xml_id == xml_id) \
                .filter(XmlNodeInstModel.parent_id == parent.id) \
                .filter(parent_name.node_id == parent.node_id) \
                .filter(parent_name.code == parent.code)

        if filters and len(filters) > 0:
            value = filters[0].get('value', None)
            if value:
                start_date = strptime(value, DATE_FORMAT_SYSTEM)
                nodes = nodes \
                    .filter(XmlNodeInstModel.start_date <= start_date) \
                    .filter(or_(XmlNodeInstModel.end_date.is_(None), XmlNodeInstModel.end_date > start_date))

        nodes.all()
        node_inst_ids = [o.id for o in nodes]

        children_count_by_id = self.db.query(XmlNodeInstModel.parent_id, func.count(XmlNodeInstModel.id)) \
            .filter(XmlNodeInstModel.parent_id.in_(node_inst_ids)) \
            .group_by(XmlNodeInstModel.parent_id) \
            .all()

        return self._parse_node(node_inst_ids, nodes, parent_id, dict(children_count_by_id))

    def load_node_from_library(self, library_id, node_type, parent_id=None):
        if parent_id == '0':
            parent_id = None

        nodes = self.db.query(XmlNodeInstModel) \
            .join(XmlNodeInstModel.node) \
            .options(joinedload(XmlNodeInstModel.node)) \
            .filter(XmlNodeInstModel.user_library_id == library_id) \
            .filter(XmlNodeInstModel.node_id == node_type) \
            .filter(XmlNodeInstModel.parent_id == parent_id) \
            .all()

        node_inst_ids = [o.id for o in nodes]

        children_count_by_id = self.db.query(XmlNodeInstModel.parent_id, func.count(XmlNodeInstModel.id)) \
            .filter(XmlNodeInstModel.user_library_id == library_id) \
            .filter(XmlNodeInstModel.parent_id.in_(node_inst_ids)) \
            .group_by(XmlNodeInstModel.parent_id) \
            .all()

        return self._parse_node(node_inst_ids, nodes, parent_id, dict(children_count_by_id))

    def _parse_node(self, node_inst_ids, nodes, parent_node_id, children_count_by_id):
        code_attrs = self.db.query(XmlNodeAttrValModel) \
            .join(XmlNodeAttrValModel.attr) \
            .options(joinedload(XmlNodeAttrValModel.attr).joinedload(XmlNodeAttrModel.widget)) \
            .filter(XmlNodeAttrValModel.node_inst_id.in_(node_inst_ids)) \
            .filter(XmlNodeAttrModel.name.in_([XmlNodeAttrEnum.DESCRIPTION,
                                               XmlNodeAttrEnum.CODE,
                                               XmlNodeAttrEnum.LOCATION_CODE,
                                               XmlNodeAttrEnum.LATITUDE,
                                               XmlNodeAttrEnum.LONGITUDE,
                                               XmlNodeAttrEnum.SITE,
                                               XmlNodeAttrEnum.SENSOR,
                                               XmlNodeAttrEnum.SAMPLE_RATE])) \
            .order_by(XmlNodeAttrValModel.node_inst_id) \
            .all()

        attrs_by_inst_id = OrderedDict((k, list(v)) for k, v in groupby(code_attrs, lambda r: r.node_inst_id))

        all_nodes = []

        for node_inst in nodes:
            attrs = {}
            if node_inst.id in attrs_by_inst_id:
                for attr_inst in attrs_by_inst_id[node_inst.id]:
                    attrs[attr_inst.attr.name] = attr_inst.value_obj

            code = attrs.get(XmlNodeAttrEnum.CODE, 'UKN')
            location_code = attrs.get(XmlNodeAttrEnum.LOCATION_CODE, None)
            description = attrs.get(XmlNodeAttrEnum.DESCRIPTION, '')
            latitude = attrs.get(XmlNodeAttrEnum.LATITUDE, '')
            longitude = attrs.get(XmlNodeAttrEnum.LONGITUDE, '')
            site = attrs.get(XmlNodeAttrEnum.SITE, '')
            sensor = attrs.get(XmlNodeAttrEnum.SENSOR, '')
            sample_rate = attrs.get(XmlNodeAttrEnum.SAMPLE_RATE, '')

            all_nodes.append({
                'id': node_inst.id,
                'code': code,
                'name': "%s.%s" % (
                    location_code if location_code else "--",
                    code) if node_inst.node_id == XmlNodeEnum.CHANNEL else code,
                'start': node_inst.start_date,
                'location_code': location_code,
                'end': node_inst.end_date,
                'latitude': latitude,
                'longitude': longitude,
                'sample_rate': sample_rate,
                'site': site.name if site else '',
                'sensor': sensor.description if sensor else '',
                'parentId': parent_node_id,
                'leaf': node_inst.node_id == XmlNodeEnum.CHANNEL,
                'nodeType': node_inst.node.id,
                'description': description,
                'has_children': node_inst.id in children_count_by_id
            })
        data = sorted(all_nodes, key=lambda r: r['name'].upper())

        last_location_code = 0
        for i in range(len(data)):
            record = data[i]
            record['index'] = i + 1
            record['last'] = True if last_location_code != record['location_code'] and record[
                'nodeType'] != XmlNodeEnum.NETWORK else False
            last_location_code = record['location_code']

        return data

    def _create_default_node_for_xml(self, xml_id, node_type, parent, utc_now, index=None):
        code, num_children, child_node_id, required_attrs = self.config.get_cfg_by_node_id(int(node_type))

        code = code + str(index) if index is not None else code

        node_inst = XmlNodeInstModel(xml_id=xml_id, code=code, node_id=node_type)

        self._create_attributes(required_attrs, code, utc_now, node_inst, parent=parent)

        node_inst.parent = parent

        if num_children:
            for i in range(num_children):
                self._create_default_node_for_xml(xml_id, child_node_id, node_inst, utc_now, i)

        return node_inst

    def _create_default_node_for_library(self, node_type, library_id, parent):
        code, num_children, child_node_type, required_attrs = self.config.get_cfg_by_node_id(node_type)

        node_inst = XmlNodeInstModel()
        node_inst.code = code
        node_inst.user_library_id = library_id
        node_inst.node_id = node_type
        node_inst.parent_id = parent.id if parent else None

        utc_now = datetime.utcnow().replace(microsecond=0)
        self._create_attributes(required_attrs, code, utc_now, node_inst, parent=parent)
        return node_inst

    def _create_attributes(self, required_attrs, code, utc_now, node_inst, parent=None):
        attrs_to_propagate = {}
        if parent and parent.node_id == XmlNodeEnum.STATION:
            parent_attr_values = self.db.query(XmlNodeAttrValModel) \
                .join(XmlNodeAttrValModel.attr) \
                .options(joinedload(XmlNodeAttrValModel.attr)) \
                .filter(XmlNodeAttrValModel.node_inst_id == parent.id) \
                .filter(XmlNodeAttrModel.name.in_([XmlNodeAttrEnum.LATITUDE,
                                                   XmlNodeAttrEnum.LONGITUDE,
                                                   XmlNodeAttrEnum.ELEVATION])) \
                .all()
            for attr_val in parent_attr_values:
                attrs_to_propagate[attr_val.attr.name] = attr_val.value_obj

        for required_attr in set(required_attrs):
            attr = self.db.query(XmlNodeAttrModel).filter(XmlNodeAttrModel.name == required_attr).first()
            if required_attr == XmlNodeAttrEnum.CODE:
                val = code
            elif required_attr == XmlNodeAttrEnum.CREATION_DATE:
                val = UTCDateTime(utc_now)
            elif required_attr == XmlNodeAttrEnum.ELEVATION:
                val = Distance(attrs_to_propagate.get(attr.name, 0))
            else:
                if attr.widget.name in [XmlNodeAttrWindetsEnum.FLOAT, XmlNodeAttrWindetsEnum.INT]:
                    val = 0
                elif attr.widget.name == XmlNodeAttrWindetsEnum.LATITUDE:
                    val = Latitude(attrs_to_propagate.get(attr.name, 0))
                elif attr.widget.name == XmlNodeAttrWindetsEnum.LONGITUDE:
                    val = Longitude(attrs_to_propagate.get(attr.name, 0))
                elif attr.widget.name == XmlNodeAttrWindetsEnum.DATE:
                    val = UTCDateTime(0)
                elif attr.widget.name == XmlNodeAttrWindetsEnum.SITE:
                    val = Site('')
                else:
                    val = ''
            self.db.add(XmlNodeAttrValModel(node_inst=node_inst, attr=attr, value_obj=val))

    def _clone_node_and_active_children(self, node_inst, utc_now, xml_id, parent, library_id):
        clone_obj = node_inst.__class__()
        clone_obj.xml_id = xml_id
        clone_obj.user_library_id = library_id
        clone_obj.node_id = node_inst.node_id
        clone_obj.start_date = node_inst.start_date
        clone_obj.end_date = node_inst.end_date
        clone_obj.code = node_inst.code
        clone_obj.parent = parent

        for node_attr_val in node_inst.attr_vals:
            clone_node_attr_val = XmlNodeAttrValModel()
            clone_node_attr_val.attr_id = node_attr_val.attr_id
            clone_node_attr_val.node_inst = clone_obj
            clone_node_attr_val.value = node_attr_val.value
            clone_obj.attr_vals.append(clone_node_attr_val)

        children = node_inst.children \
            .filter(or_(XmlNodeInstModel.end_date.is_(None), XmlNodeInstModel.end_date > utc_now))
        for child in children:
            self._clone_node_and_active_children(child, utc_now, xml_id, clone_obj, library_id)

        return clone_obj

    def _update_xml_datetime(self, xml_id):
        self.db.query(XmlModel) \
            .filter(XmlModel.id == xml_id) \
            .update({'updated_at': datetime.utcnow()})

    def _update_library_datetime(self, library_id):
        self.db.query(UserLibraryModel) \
            .filter(UserLibraryModel.id == library_id) \
            .update({'updated_at': datetime.utcnow()})

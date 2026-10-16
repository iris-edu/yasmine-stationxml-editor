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

from _collections import OrderedDict
from datetime import datetime
import logging
import time
from obspy import UTCDateTime
from obspy.core.inventory import Longitude, Latitude, Site, Distance
from sqlalchemy.orm import joinedload, aliased
from sqlalchemy.sql.expression import or_
from yasmine.app.enums.xml_node import XmlNodeAttrEnum, XmlNodeAttrWindetsEnum, XmlNodeEnum
from yasmine.app.exceptions.exceptions import BusinessException
from yasmine.app.models import XmlNodeInstModel, XmlModel, XmlNodeAttrModel, XmlNodeAttrValModel, UserLibraryModel
from yasmine.app.utils.db import db_transaction
from yasmine.app.utils.facade import HandlerMixin
from yasmine.app.utils.date import parse_naive_datetime, get_utcnow_naive
from sqlalchemy import func
from itertools import groupby


logger = logging.getLogger(__name__)
_SLOW_LOAD_MS = 500
_MAP_ATTRS = (
    XmlNodeAttrEnum.CODE,
    XmlNodeAttrEnum.LOCATION_CODE,
    XmlNodeAttrEnum.LATITUDE,
    XmlNodeAttrEnum.LONGITUDE,
    XmlNodeAttrEnum.AZIMUTH,
    XmlNodeAttrEnum.DIP,
)
_MAP_MIN_SPAN = 0.2
_MAP_PAD = 0.2


def _map_number(value):
    if value is None or value == '':
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float('inf'), float('-inf')):
        return None
    return number


def _map_code(value, fallback):
    if value is None or value == '':
        return fallback or ''
    return str(value)


def _location_label(value):
    if value is None or str(value).strip() == '':
        return '--'
    return str(value).strip()


def _active_at(node, epoch):
    if epoch is None:
        return True
    if node.start_date is None or node.start_date > epoch:
        return False
    if node.end_date is not None and node.end_date <= epoch:
        return False
    return True


def _epoch_entry(node):
    return {'start': node.start_date, 'end': node.end_date}


def _sorted_unique_epochs(entries):
    seen = set()
    unique = []
    for entry in entries:
        key = (entry.get('start'), entry.get('end'))
        if key in seen:
            continue
        seen.add(key)
        unique.append(entry)
    unique.sort(key=lambda row: (
        row['start'] is None,
        row['start'] or datetime.min,
        row['end'] is None,
        row['end'] or datetime.max,
    ))
    return unique


_ORIENTATION_ORDER = {'Z': 0, 'N': 1, 'E': 2, '1': 3, '2': 4}
_ORIENTATION_FALLBACK = 100


def _split_channel_code(code):
    """Split a SEED channel code into band+instrument and orientation suffix."""
    text = '' if code is None else str(code).upper()
    length = len(text)
    if length == 0:
        return '', ''
    if length == 1:
        return '', text
    if length == 2:
        return text[0], text[1]
    return text[:2], text[2:]


def _orientation_rank(orientation):
    if not orientation:
        return _ORIENTATION_FALLBACK
    return _ORIENTATION_ORDER.get(orientation[0], _ORIENTATION_FALLBACK)


def _node_sort_key(record):
    """Sort key for builder/library children: channels by loc, BI, start, orient."""
    if record.get('nodeType') == XmlNodeEnum.CHANNEL:
        location = record.get('location_code')
        location = '' if location is None else str(location).upper()
        band_instrument, orientation = _split_channel_code(record.get('code'))
        start = record.get('start')
        return (
            location,
            band_instrument,
            start is None,
            start or datetime.min,
            _orientation_rank(orientation),
            orientation,
        )
    name = record.get('name') or ''
    return (str(name).upper(),)


def _orientation_of(bag):
    """Azimuth/dip for map QC tooltips (channel nodes)."""
    azimuth = _map_number(bag.get(XmlNodeAttrEnum.AZIMUTH))
    dip = _map_number(bag.get(XmlNodeAttrEnum.DIP))
    flags = []
    if azimuth is None:
        flags.append('missing_azimuth')
    elif azimuth < 0 or azimuth >= 360:
        flags.append('azimuth_out_of_range')
    if dip is None:
        flags.append('missing_dip')
    elif dip < -90 or dip > 90:
        flags.append('dip_out_of_range')
    return {
        'azimuth': azimuth,
        'dip': dip,
        'qc': flags,
    }


def _contiguous_longitudes(longitudes):
    if not longitudes:
        return []
    raw_span = max(longitudes) - min(longitudes)
    shifted = [lon + 360.0 if lon < 0 else lon for lon in longitudes]
    shift_span = max(shifted) - min(shifted)
    if raw_span <= 180 or raw_span <= shift_span:
        return list(longitudes)
    return shifted


def padded_extent(points):
    """Network aperture plus 20 percent on each side. None when there are no points."""
    if not points:
        return None
    latitudes = [point[0] for point in points]
    longitudes = _contiguous_longitudes([point[1] for point in points])
    south, north = min(latitudes), max(latitudes)
    west, east = min(longitudes), max(longitudes)
    lat_span = north - south
    lon_span = east - west
    if lat_span < _MAP_MIN_SPAN:
        mid = (south + north) / 2.0
        south = mid - _MAP_MIN_SPAN / 2.0
        north = mid + _MAP_MIN_SPAN / 2.0
        lat_span = _MAP_MIN_SPAN
    if lon_span < _MAP_MIN_SPAN:
        mid = (west + east) / 2.0
        west = mid - _MAP_MIN_SPAN / 2.0
        east = mid + _MAP_MIN_SPAN / 2.0
        lon_span = _MAP_MIN_SPAN
    south -= lat_span * _MAP_PAD
    north += lat_span * _MAP_PAD
    west -= lon_span * _MAP_PAD
    east += lon_span * _MAP_PAD
    return {
        'south': max(-90.0, south),
        'west': west,
        'north': min(90.0, north),
        'east': east,
    }


class NodeService(HandlerMixin):
    def delete_node_from_xml(self, xml_id, node_id):
        with db_transaction(self.db):
            self.db.query(XmlNodeInstModel) \
                .filter(XmlNodeInstModel.xml_id == xml_id,
                        XmlNodeInstModel.id == node_id) \
                .delete()
            self._update_xml_datetime(xml_id)

    def descendant_node_ids(self, node_id, xml_id=None, library_id=None):
        """Return *node_id* plus descendant XmlNodeInst ids in one document/library."""
        try:
            node_id = int(node_id)
        except (TypeError, ValueError):
            return []
        query = self.db.query(XmlNodeInstModel.id, XmlNodeInstModel.parent_id)
        if xml_id is not None:
            try:
                xml_id = int(xml_id)
            except (TypeError, ValueError):
                return []
            query = query.filter(XmlNodeInstModel.xml_id == xml_id)
        elif library_id is not None:
            try:
                library_id = int(library_id)
            except (TypeError, ValueError):
                return []
            query = query.filter(XmlNodeInstModel.user_library_id == library_id)
        else:
            return []
        nodes = query.all()
        children = {}
        for nid, parent_id in nodes:
            children.setdefault(parent_id, []).append(nid)
        collected = []
        stack = [node_id]
        seen = set()
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            collected.append(current)
            stack.extend(children.get(current, []))
        return collected

    def extension_summary_for_node(
            self, node_id, xml_id=None, library_id=None, include_descendants=True):
        """Read-only sidecar summary for delete confirm / Extensions panel."""
        from yasmine.app.utils.stationxml_migration import summarize_extension_sidecar

        try:
            node_id = int(node_id)
        except (TypeError, ValueError):
            return None
        ids = (
            self.descendant_node_ids(node_id, xml_id=xml_id, library_id=library_id)
            if include_descendants else [node_id]
        )
        if not ids:
            return {
                'nodeId': node_id,
                'sidecarNodeCount': 0,
                'attributeCount': 0,
                'elementCount': 0,
                'nodes': [],
            }
        query = self.db.query(XmlNodeInstModel).filter(XmlNodeInstModel.id.in_(ids))
        if xml_id is not None:
            query = query.filter(XmlNodeInstModel.xml_id == int(xml_id))
        elif library_id is not None:
            query = query.filter(XmlNodeInstModel.user_library_id == int(library_id))
        rows = query.all()
        nodes = []
        attr_total = 0
        elem_total = 0
        for row in rows:
            if not row.extension_sidecar:
                continue
            summary = summarize_extension_sidecar(row.extension_sidecar)
            if summary.get('attributeCount') or summary.get('elementCount'):
                nodes.append({
                    'id': row.id,
                    'code': row.code,
                    'nodeType': row.node_id,
                    'attributeCount': summary['attributeCount'],
                    'elementCount': summary['elementCount'],
                    'attributes': summary.get('attributes') or [],
                    'elements': summary.get('elements') or [],
                })
                attr_total += summary['attributeCount']
                elem_total += summary['elementCount']
        return {
            'nodeId': node_id,
            'sidecarNodeCount': len(nodes),
            'attributeCount': attr_total,
            'elementCount': elem_total,
            'nodes': nodes,
        }

    def delete_node_from_library(self, library_id, node_type, node_inst_id):
        with db_transaction(self.db):
            self.db.query(XmlNodeInstModel) \
                .filter(XmlNodeInstModel.user_library_id == library_id,
                        XmlNodeInstModel.id == node_inst_id,
                        XmlNodeInstModel.node_id == node_type) \
                .delete()
            self._update_library_datetime(library_id)

    def create_default_node_for_xml(self, xml_id, node_type, parent_id):
        with db_transaction(self.db):
            parent = self.db.get(XmlNodeInstModel, parent_id) if parent_id else None
            utc_now = get_utcnow_naive().replace(microsecond=0)
            node = self._create_default_node_for_xml(xml_id, node_type, parent, utc_now)
            self.db.add(node)
            self._update_xml_datetime(xml_id)
        return node.id

    def create_default_node_for_library(self, library_id, node_type, parent_id):
        with db_transaction(self.db):
            parent = self.db.get(XmlNodeInstModel, parent_id) if parent_id else None
            node = self._create_default_node_for_library(node_type, library_id, parent)
            self.db.add(node)
            self._update_library_datetime(library_id)
        return node.id

    def add_node_to_library(self, library_id, node_id):
        with db_transaction(self.db):
            node_to_clone = self.db.get(XmlNodeInstModel, node_id)
            if node_to_clone is None:
                raise BusinessException('Node not found')
            utc_now = get_utcnow_naive().replace(microsecond=0)
            new_node = self._clone_node_and_active_children(node_to_clone, utc_now, None, None, library_id)
            self.db.add(new_node)
            self._update_library_datetime(library_id)
        return new_node.id

    def add_node_to_xml(self, xml_id, node_id, parent_id):
        with db_transaction(self.db):
            node_to_clone = self.db.get(XmlNodeInstModel, node_id)
            if node_to_clone is None:
                raise BusinessException('Node not found')
            parent = self.db.get(XmlNodeInstModel, parent_id) if parent_id else None
            utc_now = get_utcnow_naive().replace(microsecond=0)
            new_node = self._clone_node_and_active_children(node_to_clone, utc_now, xml_id, parent, None)
            self.db.add(new_node)
            self._update_xml_datetime(xml_id)
        return new_node.id

    def load_node_from_xml(self, xml_id, parent_id, filters):
        if parent_id in (None, '', '0', 0):
            nodes = self.db.query(XmlNodeInstModel) \
                .join(XmlNodeInstModel.node) \
                .options(joinedload(XmlNodeInstModel.node)) \
                .filter(XmlNodeInstModel.xml_id == xml_id) \
                .filter(XmlNodeInstModel.parent_id.is_(None))
        else:
            parent = self.db.get(XmlNodeInstModel, int(parent_id))
            if parent is None:
                return []
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
                start_date = parse_naive_datetime(value)
                nodes = nodes \
                    .filter(XmlNodeInstModel.start_date <= start_date) \
                    .filter(or_(XmlNodeInstModel.end_date.is_(None), XmlNodeInstModel.end_date > start_date))

        started = time.perf_counter()
        nodes = nodes.all()
        if not nodes:
            return []
        node_inst_ids = [o.id for o in nodes]

        children_count_by_id = self.db.query(XmlNodeInstModel.parent_id, func.count(XmlNodeInstModel.id)) \
            .filter(XmlNodeInstModel.parent_id.in_(node_inst_ids)) \
            .group_by(XmlNodeInstModel.parent_id) \
            .all()

        parsed = self._parse_node(node_inst_ids, nodes, parent_id, dict(children_count_by_id))
        self._log_slow_load(
            'load_node_from_xml', started,
            xml_id=xml_id, parent_id=parent_id, nodes=len(nodes),
        )
        return parsed

    def load_map(self, xml_id, node_id, epoch=None, include_channels=False):
        try:
            xml_id = int(xml_id)
            node_id = 0 if node_id in (None, '', '0', 0) else int(node_id)
        except (TypeError, ValueError):
            return None
        selected = None
        if node_id:
            selected = self.db.get(XmlNodeInstModel, node_id)
            if selected is None or selected.xml_id != xml_id:
                return None
            if selected.node_id not in (
                XmlNodeEnum.NETWORK, XmlNodeEnum.STATION, XmlNodeEnum.CHANNEL
            ):
                return None

        node_types = [XmlNodeEnum.NETWORK, XmlNodeEnum.STATION]
        if include_channels:
            node_types.append(XmlNodeEnum.CHANNEL)
        nodes = self.db.query(XmlNodeInstModel) \
            .filter(XmlNodeInstModel.xml_id == xml_id) \
            .filter(XmlNodeInstModel.node_id.in_(node_types)) \
            .all()
        by_id = {node.id: node for node in nodes}
        values = {}
        if by_id:
            attr_rows = self.db.query(XmlNodeAttrValModel) \
                .join(XmlNodeAttrValModel.attr) \
                .options(joinedload(XmlNodeAttrValModel.attr)) \
                .filter(XmlNodeAttrValModel.node_inst_id.in_(list(by_id))) \
                .filter(XmlNodeAttrModel.name.in_(_MAP_ATTRS)) \
                .all()
            for attr in attr_rows:
                try:
                    values.setdefault(attr.node_inst_id, {})[attr.attr.name] = attr.value_obj
                except Exception:
                    continue

        def code_of(node):
            if node is None:
                return ''
            stored = values.get(node.id, {}).get(XmlNodeAttrEnum.CODE)
            return _map_code(stored, node.code)

        def coords_of(node):
            bag = values.get(node.id, {})
            latitude = _map_number(bag.get(XmlNodeAttrEnum.LATITUDE))
            longitude = _map_number(bag.get(XmlNodeAttrEnum.LONGITUDE))
            if latitude is None or longitude is None:
                return None
            if latitude < -90 or latitude > 90 or longitude < -180 or longitude > 180:
                return None
            return latitude, longitude

        def station_label(station):
            network = by_id.get(station.parent_id)
            return '%s.%s' % (code_of(network), code_of(station))

        def channel_label(channel):
            station = by_id.get(channel.parent_id)
            network = by_id.get(station.parent_id) if station is not None else None
            location = _location_label(
                values.get(channel.id, {}).get(XmlNodeAttrEnum.LOCATION_CODE)
            )
            return '%s.%s.%s.%s' % (
                code_of(network), code_of(station), location, code_of(channel)
            )

        def station_row(station):
            latitude, longitude = coords_of(station)
            label = station_label(station)
            return {
                'id': station.id,
                'latitude': latitude,
                'longitude': longitude,
                'label': label,
                'epochs': station_epochs.get(label, [_epoch_entry(station)]),
                'qc': [],
            }

        def channel_row(channel):
            latitude, longitude = coords_of(channel)
            label = channel_label(channel)
            orientation = _orientation_of(values.get(channel.id, {}))
            return {
                'id': channel.id,
                'latitude': latitude,
                'longitude': longitude,
                'label': label,
                'epochs': channel_epochs.get(label, [_epoch_entry(channel)]),
                'azimuth': orientation['azimuth'],
                'dip': orientation['dip'],
                'qc': orientation['qc'],
            }

        stations = [node for node in nodes if node.node_id == XmlNodeEnum.STATION]
        channels = [node for node in nodes if node.node_id == XmlNodeEnum.CHANNEL]
        station_epochs = {}
        for station in stations:
            label = station_label(station)
            station_epochs.setdefault(label, []).append(_epoch_entry(station))
        station_epochs = {
            label: _sorted_unique_epochs(entries)
            for label, entries in station_epochs.items()
        }
        channel_epochs = {}
        for channel in channels:
            label = channel_label(channel)
            channel_epochs.setdefault(label, []).append(_epoch_entry(channel))
        channel_epochs = {
            label: _sorted_unique_epochs(entries)
            for label, entries in channel_epochs.items()
        }

        if selected is None:
            marker_stations = [node for node in stations if _active_at(node, epoch)]
            active_station_ids = {node.id for node in marker_stations}
            marker_channels = [
                node for node in channels
                if node.parent_id in active_station_ids and _active_at(node, epoch)
            ]
            extent_stations = marker_stations
        elif selected.node_id == XmlNodeEnum.NETWORK:
            marker_stations = [
                node for node in stations
                if node.parent_id == selected.id and _active_at(node, epoch)
            ]
            active_station_ids = {node.id for node in marker_stations}
            marker_channels = [
                node for node in channels
                if node.parent_id in active_station_ids and _active_at(node, epoch)
            ]
            extent_stations = marker_stations
        elif selected.node_id == XmlNodeEnum.STATION:
            marker_stations = [selected] if _active_at(selected, epoch) else []
            marker_channels = [
                node for node in channels
                if marker_stations and node.parent_id == selected.id and _active_at(node, epoch)
            ]
            extent_stations = [
                node for node in stations
                if node.parent_id == selected.parent_id and _active_at(node, epoch)
            ]
        else:
            parent = by_id.get(selected.parent_id)
            marker_channels = [selected] if _active_at(selected, epoch) else []
            marker_stations = [parent] if parent is not None else []
            network_id = parent.parent_id if parent is not None else None
            extent_stations = [
                node for node in stations
                if node.parent_id == network_id and _active_at(node, epoch)
            ]

        if not include_channels:
            marker_channels = []

        station_rows = [
            station_row(node) for node in marker_stations if coords_of(node) is not None
        ]
        channel_rows = [
            channel_row(node) for node in marker_channels if coords_of(node) is not None
        ]
        extent_points = []
        for node in extent_stations:
            point = coords_of(node)
            if point is not None:
                extent_points.append(point)
        if not extent_points:
            extent_points = [
                (row['latitude'], row['longitude'])
                for row in station_rows + channel_rows
            ]
        return {
            'stations': station_rows,
            'channels': channel_rows,
            'extent': padded_extent(extent_points),
        }

    def load_node_from_library(self, library_id, node_type, parent_id=None):
        if parent_id == '0':
            parent_id = None

        started = time.perf_counter()
        nodes = self.db.query(XmlNodeInstModel) \
            .join(XmlNodeInstModel.node) \
            .options(joinedload(XmlNodeInstModel.node)) \
            .filter(XmlNodeInstModel.user_library_id == library_id) \
            .filter(XmlNodeInstModel.node_id == node_type) \
            .filter(XmlNodeInstModel.parent_id == parent_id) \
            .all()

        if not nodes:
            return []
        node_inst_ids = [o.id for o in nodes]

        children_count_by_id = self.db.query(XmlNodeInstModel.parent_id, func.count(XmlNodeInstModel.id)) \
            .filter(XmlNodeInstModel.user_library_id == library_id) \
            .filter(XmlNodeInstModel.parent_id.in_(node_inst_ids)) \
            .group_by(XmlNodeInstModel.parent_id) \
            .all()

        parsed = self._parse_node(node_inst_ids, nodes, parent_id, dict(children_count_by_id))
        self._log_slow_load(
            'load_node_from_library', started,
            library_id=library_id, node_type=node_type, parent_id=parent_id,
            nodes=len(nodes),
        )
        return parsed

    def _log_slow_load(self, operation, started, **fields):
        elapsed_ms = (time.perf_counter() - started) * 1000
        if elapsed_ms < _SLOW_LOAD_MS:
            return
        extras = ' '.join('%s=%s' % item for item in fields.items())
        logger.warning('slow %s elapsed_ms=%.1f %s', operation, elapsed_ms, extras)

    def _parse_node(self, node_inst_ids, nodes, parent_node_id, children_count_by_id):
        if not node_inst_ids:
            return []
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
        data = sorted(all_nodes, key=_node_sort_key)

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

        utc_now = get_utcnow_naive().replace(microsecond=0)
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

        for required_attr in set(required_attrs or []):
            attr = self.db.query(XmlNodeAttrModel).filter(XmlNodeAttrModel.name == required_attr).first()
            if attr is None:
                continue
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
        clone_obj.extension_sidecar = node_inst.extension_sidecar
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
            .update({'updated_at': get_utcnow_naive()})

    def _update_library_datetime(self, library_id):
        self.db.query(UserLibraryModel) \
            .filter(UserLibraryModel.id == library_id) \
            .update({'updated_at': get_utcnow_naive()})

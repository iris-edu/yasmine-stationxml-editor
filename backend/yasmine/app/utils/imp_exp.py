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
# 2026-09-27, version 4.4.0-beta: ASGSR, Alexey Emanov
#
# ****************************************************************************/


from _collections import OrderedDict
from builtins import Exception
from itertools import groupby
import base64
import datetime
import gc
import inspect
import io
import json
import logging
import threading
import traceback

from obspy import UTCDateTime
from obspy.core.inventory.channel import Channel
from obspy.core.inventory.network import Network
from obspy.core.inventory.station import Station
from obspy.core.inventory.inventory import read_inventory, Inventory
from obspy.core.inventory.util import Site
from lxml import etree
from slugify import slugify
from sqlalchemy.orm import joinedload
from tornado.web import HTTPError

from yasmine.app.enums.xml_node import XmlNodeEnum
from yasmine.app.models.inventory import XmlModel, XmlNodeInstModel, XmlNodeAttrRelationModel, XmlNodeAttrValModel
from yasmine.app.models.user_library import UserLibraryModel
from yasmine.app.utils.db import db_transaction
from yasmine.app.utils.facade import HandlerMixin
from yasmine.app.utils.stationxml_validation import (
    STATIONXML_IMPORT_ERROR,
    ensure_importable_stationxml,
    validate_stationxml_12,
)
from yasmine.app.utils.stationxml_codec import (
    extract_inventory_sidecars,
    iter_stationxml_pieces,
    prepare_stationxml_for_obspy,
    serialize_inventory_12,
)


stationxml_import_lock = threading.Lock()


class ImportStationXml(HandlerMixin):
    def __init__(self, name, file_obj, *_, **__):
        self.file_obj = file_obj
        self.name = name
        super(ImportStationXml, self).__init__(*_, **__)

    def instantiate_node(self, data, node_id, attrs, extension_sidecar=None):

        inst_node = XmlNodeInstModel(node_id=node_id,
                                     code=data.code,
                                     start_date=data.start_date.datetime if data.start_date else None,
                                     end_date=data.end_date.datetime if data.end_date else None,
                                     extension_sidecar=extension_sidecar)
        for attr in attrs:
            if hasattr(data, attr.name):
                value = getattr(data, attr.name)
                if value is not None:
                    inst_node.attr_vals.append(XmlNodeAttrValModel(attr=attr,
                                                                   node_inst=inst_node,
                                                                   value_obj=getattr(data, attr.name))
                                               )
        return inst_node

    @staticmethod
    def restore_span_only_data_availability(data, sidecar_record):
        compatibility = sidecar_record.get('compatibility', {})
        availability = getattr(data, 'data_availability', None)
        if (
            availability is not None
            and compatibility.get('dataAvailabilityExtentAbsent')
        ):
            availability.start = None
            availability.end = None

    def _attr_map(self):
        all_attrs = self.db.query(XmlNodeAttrRelationModel).options(
            joinedload(XmlNodeAttrRelationModel.attr)
        ).all()
        all_attrs.sort(key=lambda x: x.node_id, reverse=False)
        return OrderedDict(
            (k, [o.attr for o in list(v)])
            for k, v in groupby(all_attrs, lambda r: r.node_id)
        )

    def _release_import_memory(self):
        self.db.expunge_all()
        gc.collect()

    def run(self):
        if not stationxml_import_lock.acquire(blocking=False):
            raise ValueError(
                'Another StationXML import is already running. '
                'Wait until it finishes before starting another.'
            )
        try:
            return self._import_document()
        finally:
            stationxml_import_lock.release()

    def _import_document(self):
        xml_bytes = self.file_obj.read()
        ensure_importable_stationxml(xml_bytes)
        xml_id = None
        network_id = None
        logger = logging.getLogger(__name__)
        station_count = 0
        try:
            for piece in iter_stationxml_pieces(xml_bytes):
                kind = piece['kind']
                if kind == 'network':
                    xml_id, network_id = self._store_network(piece, xml_id)
                elif kind == 'station':
                    station_count += 1
                    self._store_station(piece, xml_id, network_id)
                    if station_count % 25 == 0:
                        logger.info('Imported %s stations', station_count)
                elif kind == 'root' and xml_id is not None and piece.get('sidecar'):
                    with db_transaction(self.db):
                        stored = self.db.get(XmlModel, xml_id)
                        stored.extension_sidecar = piece['sidecar']
                    self._release_import_memory()
            if xml_id is None:
                raise ValueError(STATIONXML_IMPORT_ERROR)
            logger.info('Imported %s stations', station_count)
            return self.db.get(XmlModel, xml_id)
        except Exception:
            self._discard_partial_import(xml_id)
            raise

    def _discard_partial_import(self, xml_id):
        if not xml_id:
            return
        try:
            self.db.rollback()
        except Exception:
            pass
        self.db.expunge_all()
        with db_transaction(self.db):
            stored = self.db.get(XmlModel, xml_id)
            if stored is not None:
                self.db.delete(stored)

    def _store_network(self, piece, xml_id):
        attrs_by_node_id = self._attr_map()
        inv = read_inventory(io.BytesIO(piece['xml']))
        try:
            record = {
                'sidecar': piece.get('sidecar'),
                'compatibility': piece.get('compatibility') or {},
            }
            network = inv.networks[0] if inv.networks else None
            if network is not None:
                self.restore_span_only_data_availability(network, record)
            with db_transaction(self.db):
                if xml_id is None:
                    xml = XmlModel(
                        name=self.name,
                        source=inv.source,
                        sender=inv.sender,
                        module=inv.module,
                        uri=inv.module_uri,
                        created_at=inv.created.datetime,
                    )
                    self.db.add(xml)
                    self.db.flush()
                    xml_id = xml.id
                else:
                    xml = self.db.get(XmlModel, xml_id)
                network_id = None
                if network is not None:
                    network_inst_node = self.instantiate_node(
                        network,
                        XmlNodeEnum.NETWORK,
                        attrs_by_node_id[XmlNodeEnum.NETWORK],
                        record.get('sidecar'),
                    )
                    xml.nodes.append(network_inst_node)
                    self.db.flush()
                    network_id = network_inst_node.id
            return xml_id, network_id
        finally:
            del inv
            self._release_import_memory()

    def _store_station(self, piece, xml_id, network_id):
        attrs_by_node_id = self._attr_map()
        inv = read_inventory(io.BytesIO(piece['xml']))
        try:
            station = inv.networks[0].stations[0]
            record = piece.get('record') or {}
            self.restore_span_only_data_availability(station, record)
            with db_transaction(self.db):
                xml = self.db.get(XmlModel, xml_id)
                network_inst_node = self.db.get(XmlNodeInstModel, network_id)
                station_inst_node = self.instantiate_node(
                    station,
                    XmlNodeEnum.STATION,
                    attrs_by_node_id[XmlNodeEnum.STATION],
                    record.get('sidecar'),
                )
                xml.nodes.append(station_inst_node)
                network_inst_node.children.append(station_inst_node)
                for channel_index, channel in enumerate(station.channels):
                    channel_records = record.get('children') or []
                    channel_record = (
                        channel_records[channel_index]
                        if channel_index < len(channel_records)
                        else {}
                    )
                    self.restore_span_only_data_availability(
                        channel, channel_record
                    )
                    channel_inst_node = self.instantiate_node(
                        channel,
                        XmlNodeEnum.CHANNEL,
                        attrs_by_node_id[XmlNodeEnum.CHANNEL],
                        channel_record.get('sidecar'),
                    )
                    xml.nodes.append(channel_inst_node)
                    station_inst_node.children.append(channel_inst_node)
        finally:
            del inv
            self._release_import_memory()


class ConvertToInventory(HandlerMixin):

    def __init__(self, xml_model_id, *_, library_id=None, **__):
        self.xml_model_id = xml_model_id
        self.library_id = library_id
        self.progress = None
        super(ConvertToInventory, self).__init__(*_, **__)

    def instantiate_node(self, clazz, attr_vals, params={}):
        node_atts = {}
        for attr_val in attr_vals:
            node_atts[attr_val.attr.name] = attr_val.value_obj
        node_atts.update(params)
        try:
            return clazz(**node_atts)
        except TypeError:
            signature = inspect.signature(clazz.__init__)
            accepted = set(signature.parameters) - {'self'}
            extra = {
                key: node_atts.pop(key)
                for key in list(node_atts)
                if key not in accepted
            }
            try:
                obj = clazz(**node_atts)
            except Exception as e:
                traceback.print_exc()
                raise HTTPError(
                    reason="Unable to instantiate %s (%s): %s" % (
                        clazz.__name__, node_atts, str(e)
                    )
                )
            for key, value in extra.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            return obj
        except Exception as e:
            traceback.print_exc()
            raise HTTPError(
                reason="Unable to instantiate %s (%s): %s" % (
                    clazz.__name__, node_atts, str(e)
                )
            )

    def _node_scope_filter(self):
        if self.library_id:
            return XmlNodeInstModel.user_library_id == self.library_id
        return XmlNodeInstModel.xml_id == self.xml_model_id

    def _ordered_nodes(self):
        return self.db.query(XmlNodeInstModel) \
            .filter(self._node_scope_filter()) \
            .order_by(XmlNodeInstModel.parent_id, XmlNodeInstModel.id) \
            .all()

    def run(self):
        if self.library_id:
            library = self.db.get(UserLibraryModel, self.library_id)
            source = ''
            sender = None
            created = library.created_at or datetime.datetime.utcnow()
            module = library.name
            uri = None
        else:
            xml = self.db.get(XmlModel, self.xml_model_id)
            source = xml.source
            sender = xml.sender
            created = xml.created_at
            module = xml.module
            uri = xml.uri

        all_attrs = self.db.query(XmlNodeAttrValModel)\
            .join(XmlNodeAttrValModel.node_inst)\
            .options(joinedload(XmlNodeAttrValModel.attr))\
            .filter(self._node_scope_filter())\
            .order_by(XmlNodeAttrValModel.node_inst_id)\
            .all()

        attrs_by_node_inst_id = OrderedDict((k, list(v)) for k, v in groupby(all_attrs, lambda r: r.node_inst_id))
        node_instances = self._ordered_nodes()
        node_inst_by_parent_id = OrderedDict((k, list(v)) for k, v in groupby(node_instances, lambda r: r.parent_id))
        networks = []
        channel_total = 0
        for nodes in node_inst_by_parent_id.values():
            for node in nodes:
                if node.node_id == XmlNodeEnum.CHANNEL:
                    channel_total += 1
        built = [0]

        def built_channel():
            built[0] += 1
            if self.progress is None or not channel_total:
                return
            if built[0] == channel_total or built[0] % 25 == 0:
                try:
                    self.progress(built[0], channel_total)
                except Exception:
                    pass

        if None in node_inst_by_parent_id:
            for network_node in node_inst_by_parent_id[None]:
                if self.library_id and network_node.node_id != XmlNodeEnum.NETWORK:
                    continue
                network_attrs = attrs_by_node_inst_id[network_node.id]
                stations = []
                for station_node in node_inst_by_parent_id.get(network_node.id, []):
                    if self.library_id and station_node.node_id != XmlNodeEnum.STATION:
                        continue
                    station_attrs = attrs_by_node_inst_id[station_node.id]
                    channels = []
                    for channel_node in node_inst_by_parent_id.get(station_node.id, []):
                        if self.library_id and channel_node.node_id != XmlNodeEnum.CHANNEL:
                            continue
                        channel_attrs = attrs_by_node_inst_id[channel_node.id]
                        channels.append(self.instantiate_node(Channel, channel_attrs))
                        built_channel()
                    stations.append(self.instantiate_node(Station, station_attrs, {'channels': channels}))
                networks.append(self.instantiate_node(Network, network_attrs, {'stations': stations}))

        return Inventory(networks, source, sender, UTCDateTime(created), module, uri)

    def sidecar_tree(self):
        if self.library_id:
            result = {'sidecar': None, 'children': []}
            networks = self.db.query(XmlNodeInstModel).filter(
                XmlNodeInstModel.user_library_id == self.library_id,
                XmlNodeInstModel.parent_id.is_(None),
            ).order_by(XmlNodeInstModel.id).all()
        else:
            xml = self.db.get(XmlModel, self.xml_model_id)
            result = {'sidecar': xml.extension_sidecar, 'children': []}
            networks = xml.nodes.filter(
                XmlNodeInstModel.parent_id.is_(None)
            ).order_by(XmlNodeInstModel.id).all()
        for network in networks:
            network_record = {
                'sidecar': network.extension_sidecar,
                'children': [],
            }
            result['children'].append(network_record)
            stations = network.children.order_by(
                XmlNodeInstModel.id
            ).all()
            for station in stations:
                station_record = {
                    'sidecar': station.extension_sidecar,
                    'children': [],
                }
                network_record['children'].append(station_record)
                channels = station.children.order_by(
                    XmlNodeInstModel.id
                ).all()
                for channel in channels:
                    station_record['children'].append({
                        'sidecar': channel.extension_sidecar,
                        'children': [],
                    })
        return result

    def convert_channel(self, node_inst_id):
        all_attrs = self.db.query(XmlNodeAttrValModel)\
            .filter(XmlNodeAttrValModel.node_inst_id == node_inst_id)\
            .all()

        attrs_by_node_inst_id = OrderedDict((k, list(v)) for k, v in groupby(all_attrs, lambda r: r.node_inst_id))
        key = int(node_inst_id)
        if key not in attrs_by_node_inst_id:
            raise ValueError('Channel not found')
        channel_attrs = attrs_by_node_inst_id[key]
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
        if channel_node is None:
            raise ValueError('Channel not found')

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
            converter = ConvertToInventory(self.xml_model_id, self)
            inv = converter.run()
        except Exception as e:
            raise HTTPError(reason="Unable to build XML: '%s'" % str(e))

        xml = self.db.get(XmlModel, self.xml_model_id)
        payload = serialize_inventory_12(
            inv,
            converter.sidecar_tree(),
            validate=False,
        )
        errors = validate_stationxml_12(payload)
        if errors:
            first = errors[0]
            raise HTTPError(
                400,
                reason='StationXML 1.2 export blocked: %s%s' % (
                    ('%s: ' % first.get('path')) if first.get('path') else '',
                    first.get('message') or 'XSD validation failed',
                ),
            )
        output = io.BytesIO(payload)

        return "%s.xml" % slugify(xml.name), output


def _requested_library_name(name):
    cleaned = (name or '').strip()
    if cleaned == 'Use the StationXML Module name':
        return ''
    return cleaned


def _unique_library_name(db, name):
    base = (name or '').strip() or 'library'
    base = base[:50]
    taken = {row[0] for row in db.query(UserLibraryModel.name).all()}
    if base not in taken:
        return base
    index = 2
    while True:
        suffix = ' (%s)' % index
        candidate = base[:50 - len(suffix)] + suffix
        if candidate not in taken:
            return candidate
        index += 1


YASMINE_LIBRARY_NS = 'urn:yasmine:user-library'


def _library_nodes_parent_first(nodes):
    by_parent = {}
    for node in nodes:
        by_parent.setdefault(node.parent_id, []).append(node)
    ordered = []

    def walk(parent_id):
        for node in by_parent.get(parent_id, []):
            ordered.append(node)
            walk(node.id)

    walk(None)
    return ordered


def _encode_attr_value(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.encode('latin-1')
    return base64.b64encode(bytes(value)).decode('ascii')


def _decode_attr_value(value):
    if value is None:
        return None
    return base64.b64decode(value)


def library_exchange_sidecar(nodes):
    """Preserve library node types and parents inside the StationXML file."""
    ordered = _library_nodes_parent_first(nodes)
    index = {node.id: position for position, node in enumerate(ordered)}
    records = []
    for node in ordered:
        records.append({
            'node_id': node.node_id,
            'parent': None if node.parent_id is None else index.get(node.parent_id),
            'code': node.code,
            'start_date': node.start_date.isoformat() if node.start_date else None,
            'end_date': node.end_date.isoformat() if node.end_date else None,
            'extension_sidecar': node.extension_sidecar,
            'attrs': [
                {
                    'attr_id': attr.attr_id,
                    'value': _encode_attr_value(attr.value),
                }
                for attr in node.attr_vals
            ],
        })
    element = etree.Element('{%s}Library' % YASMINE_LIBRARY_NS)
    element.text = json.dumps(
        {'nodes': records},
        ensure_ascii=False,
        separators=(',', ':'),
    )
    return json.dumps({
        'attributes': [],
        'elements': [{
            'parentPath': [],
            'position': 100000,
            'xml': etree.tostring(element, encoding='unicode'),
        }],
    }, separators=(',', ':'))


def read_library_layout(xml_bytes):
    document = etree.parse(io.BytesIO(xml_bytes), etree.XMLParser(
        resolve_entities=False,
        no_network=True,
    ))
    element = document.getroot().find('{%s}Library' % YASMINE_LIBRARY_NS)
    if element is None or not element.text:
        return None
    payload = json.loads(element.text)
    return payload.get('nodes') or []


def _parse_layout_date(value):
    if not value:
        return None
    return datetime.datetime.fromisoformat(value)


class ExportUserLibrary(HandlerMixin):
    def __init__(self, library_id, *_, **__):
        self.library_id = library_id
        super(ExportUserLibrary, self).__init__(*_, **__)

    def run(self):
        library = self.db.get(UserLibraryModel, self.library_id)
        if library is None:
            raise HTTPError(404, reason='User library not found')
        try:
            converter = ConvertToInventory(None, self, library_id=self.library_id)
            inv = converter.run()
        except Exception as e:
            raise HTTPError(reason="Unable to build XML: '%s'" % str(e))

        inv.module = library.name
        if not inv.networks:
            inv.networks.append(Network(code='YL'))
        nodes = self.db.query(XmlNodeInstModel).filter(
            XmlNodeInstModel.user_library_id == self.library_id
        ).all()
        tree = {
            'sidecar': library_exchange_sidecar(nodes),
            'children': [],
        }
        payload = serialize_inventory_12(
            inv,
            tree,
            validate=False,
        )
        errors = validate_stationxml_12(payload)
        if errors:
            first = errors[0]
            raise HTTPError(
                400,
                reason='StationXML 1.2 export blocked: %s%s' % (
                    ('%s: ' % first.get('path')) if first.get('path') else '',
                    first.get('message') or 'XSD validation failed',
                ),
            )
        return "%s.xml" % slugify(library.name), io.BytesIO(payload)


class ImportUserLibrary(ImportStationXml):
    """Create a user library from StationXML without an XML document."""

    def __init__(self, name, file_obj, *_, **__):
        self.requested_name = _requested_library_name(name)
        super(ImportUserLibrary, self).__init__(name or 'library', file_obj, *_, **__)

    def _restore_library_layout(self, xml_bytes, layout):
        root = etree.fromstring(xml_bytes)
        module = ''
        for child in root:
            if etree.QName(child).localname == 'Module' and child.text:
                module = child.text.strip()
                break
        library = UserLibraryModel(name=_unique_library_name(
            self.db,
            self.requested_name or module,
        ))
        created = []
        with db_transaction(self.db):
            self.db.add(library)
            self.db.flush()
            for record in layout:
                node = XmlNodeInstModel(
                    node_id=record['node_id'],
                    code=record.get('code'),
                    start_date=_parse_layout_date(record.get('start_date')),
                    end_date=_parse_layout_date(record.get('end_date')),
                    extension_sidecar=record.get('extension_sidecar'),
                    user_library_id=library.id,
                    xml_id=None,
                )
                for attr in record.get('attrs') or []:
                    value = XmlNodeAttrValModel(
                        attr_id=attr['attr_id'],
                        node_inst=node,
                    )
                    value.value = _decode_attr_value(attr.get('value'))
                    node.attr_vals.append(value)
                self.db.add(node)
                created.append(node)
            self.db.flush()
            for node, record in zip(created, layout):
                parent = record.get('parent')
                if parent is not None:
                    node.parent_id = created[parent].id
        self.db.refresh(library)
        return library

    def run(self):
        xml_bytes = self.file_obj.read()
        ensure_importable_stationxml(xml_bytes)
        layout = read_library_layout(xml_bytes)
        if layout is not None:
            return self._restore_library_layout(xml_bytes, layout)
        inv = read_inventory(io.BytesIO(
            prepare_stationxml_for_obspy(xml_bytes)
        ))
        sidecars = extract_inventory_sidecars(xml_bytes)
        library_name = _unique_library_name(
            self.db,
            self.requested_name or (inv.module or ''),
        )
        library = UserLibraryModel(name=library_name)
        with db_transaction(self.db):
            self.db.add(library)
            self.db.flush()
            library_id = library.id
        all_attrs = self.db.query(XmlNodeAttrRelationModel).options(
            joinedload(XmlNodeAttrRelationModel.attr)
        ).all()
        all_attrs.sort(key=lambda x: x.node_id, reverse=False)
        attrs_by_node_id = OrderedDict(
            (k, [o.attr for o in list(v)])
            for k, v in groupby(all_attrs, lambda r: r.node_id)
        )
        nodes = []
        for network_index, network in enumerate(inv.networks):
            network_sidecar = (
                sidecars.get('children', [])[network_index]
                if network_index < len(sidecars.get('children', []))
                else {}
            )
            self.restore_span_only_data_availability(network, network_sidecar)
            network_inst_node = self.instantiate_node(
                network,
                XmlNodeEnum.NETWORK,
                attrs_by_node_id[XmlNodeEnum.NETWORK],
                network_sidecar.get('sidecar'),
            )
            network_inst_node.user_library_id = library_id
            network_inst_node.xml_id = None
            nodes.append(network_inst_node)

            for station_index, station in enumerate(network.stations):
                station_sidecars = network_sidecar.get('children', [])
                station_sidecar = (
                    station_sidecars[station_index]
                    if station_index < len(station_sidecars)
                    else {}
                )
                self.restore_span_only_data_availability(station, station_sidecar)
                station_inst_node = self.instantiate_node(
                    station,
                    XmlNodeEnum.STATION,
                    attrs_by_node_id[XmlNodeEnum.STATION],
                    station_sidecar.get('sidecar'),
                )
                station_inst_node.user_library_id = library_id
                station_inst_node.xml_id = None
                nodes.append(station_inst_node)
                network_inst_node.children.append(station_inst_node)

                for channel_index, channel in enumerate(station.channels):
                    channel_sidecars = station_sidecar.get('children', [])
                    channel_sidecar = (
                        channel_sidecars[channel_index]
                        if channel_index < len(channel_sidecars)
                        else {}
                    )
                    self.restore_span_only_data_availability(channel, channel_sidecar)
                    channel_inst_node = self.instantiate_node(
                        channel,
                        XmlNodeEnum.CHANNEL,
                        attrs_by_node_id[XmlNodeEnum.CHANNEL],
                        channel_sidecar.get('sidecar'),
                    )
                    channel_inst_node.user_library_id = library_id
                    channel_inst_node.xml_id = None
                    nodes.append(channel_inst_node)
                    station_inst_node.children.append(channel_inst_node)

        with db_transaction(self.db):
            for node in nodes:
                self.db.add(node)
        self.db.refresh(library)
        return library

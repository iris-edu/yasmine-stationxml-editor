# 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
# Map payload: markers, SCNL labels, epoch filter, and network aperture.

import unittest
from datetime import datetime

from sqlalchemy.orm import joinedload

from yasmine.app.enums.xml_node import XmlNodeAttrEnum, XmlNodeEnum
from yasmine.app.models import XmlModel, XmlNodeAttrModel, XmlNodeAttrValModel, XmlNodeInstModel
from yasmine.app.services.node_service import NodeService, padded_extent
from yasmine.app.tests.integration.utils.integration_util import migrate_db, remove_db
from yasmine.app.utils.db import db_transaction
from yasmine.app.utils.facade import ProcessMixin


class MapFeaturesTest(unittest.TestCase, ProcessMixin):

    @classmethod
    def setUpClass(cls):
        migrate_db(cls.__name__)

    def setUp(self):
        ProcessMixin.__init__(self)
        xml = XmlModel(name='map-xml', source='t', module='m', uri='u', sender='s')
        with db_transaction(self.db):
            self.db.add(xml)
        self.db.refresh(xml)
        self.xml = xml
        service = NodeService(self)
        self.network_id = service.create_default_node_for_xml(xml.id, XmlNodeEnum.NETWORK, None)
        with db_transaction(self.db):
            self.db.query(XmlNodeInstModel) \
                .filter(XmlNodeInstModel.xml_id == xml.id) \
                .filter(XmlNodeInstModel.node_id == XmlNodeEnum.CHANNEL) \
                .delete(synchronize_session=False)
            self.db.query(XmlNodeInstModel) \
                .filter(XmlNodeInstModel.xml_id == xml.id) \
                .filter(XmlNodeInstModel.node_id == XmlNodeEnum.STATION) \
                .delete(synchronize_session=False)
        self.station_a = service.create_default_node_for_xml(xml.id, XmlNodeEnum.STATION, self.network_id)
        self.station_b = service.create_default_node_for_xml(xml.id, XmlNodeEnum.STATION, self.network_id)
        with db_transaction(self.db):
            self.db.query(XmlNodeInstModel) \
                .filter(XmlNodeInstModel.xml_id == xml.id) \
                .filter(XmlNodeInstModel.node_id == XmlNodeEnum.CHANNEL) \
                .delete(synchronize_session=False)
        self.channel_a = service.create_default_node_for_xml(xml.id, XmlNodeEnum.CHANNEL, self.station_a)
        self._set_code(self.network_id, 'AN')
        self._set_code(self.station_a, 'NVS')
        self._set_code(self.station_b, 'FAR')
        self._set_code(self.channel_a, 'EHZ')
        self._set_attr(self.channel_a, XmlNodeAttrEnum.LOCATION_CODE, '00')
        self._set_attr(self.station_a, XmlNodeAttrEnum.LATITUDE, 50.0)
        self._set_attr(self.station_a, XmlNodeAttrEnum.LONGITUDE, 80.0)
        self._set_attr(self.station_b, XmlNodeAttrEnum.LATITUDE, 52.0)
        self._set_attr(self.station_b, XmlNodeAttrEnum.LONGITUDE, 84.0)
        self._set_attr(self.channel_a, XmlNodeAttrEnum.LATITUDE, 50.01)
        self._set_attr(self.channel_a, XmlNodeAttrEnum.LONGITUDE, 80.01)
        self._set_dates(self.station_a, datetime(2020, 1, 1), datetime(2021, 1, 1))
        self._set_dates(self.station_b, datetime(2022, 1, 1), None)
        self._set_dates(self.channel_a, datetime(2020, 1, 1), datetime(2021, 1, 1))

    def test_inventory_labels_and_skips_blank_coordinates(self):
        blank = NodeService(self).create_default_node_for_xml(
            self.xml.id, XmlNodeEnum.STATION, self.network_id
        )
        self._set_code(blank, 'NIL')
        self._set_attr(blank, XmlNodeAttrEnum.LATITUDE, '')
        self._set_attr(blank, XmlNodeAttrEnum.LONGITUDE, '')
        payload = NodeService(self).load_map(self.xml.id, 0, None, include_channels=True)
        labels = [row['label'] for row in payload['stations']]
        self.assertIn('AN.NVS', labels)
        self.assertIn('AN.FAR', labels)
        self.assertNotIn('AN.NIL', labels)
        self.assertEqual(payload['channels'][0]['label'], 'AN.NVS.00.EHZ')

    def test_empty_location_uses_dashes(self):
        self._set_attr(self.channel_a, XmlNodeAttrEnum.LOCATION_CODE, '')
        payload = NodeService(self).load_map(
            self.xml.id, self.channel_a, None, include_channels=True
        )
        self.assertEqual(payload['channels'][0]['label'], 'AN.NVS.--.EHZ')
        self.assertEqual([row['label'] for row in payload['stations']], ['AN.NVS'])

    def test_scopes(self):
        service = NodeService(self)
        inventory = service.load_map(self.xml.id, 0, None, include_channels=True)
        self.assertEqual(len(inventory['stations']), 2)
        self.assertEqual(len(inventory['channels']), 1)

        network = service.load_map(self.xml.id, self.network_id, None)
        self.assertEqual(len(network['stations']), 2)

        station = service.load_map(self.xml.id, self.station_a, None, include_channels=True)
        self.assertEqual([row['label'] for row in station['stations']], ['AN.NVS'])
        self.assertEqual(len(station['channels']), 1)

        channel = service.load_map(self.xml.id, self.channel_a, None, include_channels=True)
        self.assertEqual([row['label'] for row in channel['stations']], ['AN.NVS'])
        self.assertEqual([row['id'] for row in channel['channels']], [self.channel_a])
        self.assertIsNone(service.load_map(self.xml.id, 999999, None))

    def test_epoch_filter(self):
        payload = NodeService(self).load_map(
            self.xml.id, 0, datetime(2020, 6, 1), include_channels=True
        )
        self.assertEqual([row['label'] for row in payload['stations']], ['AN.NVS'])
        self.assertEqual(len(payload['channels']), 1)

    def test_marker_payload_includes_all_operating_periods(self):
        service = NodeService(self)
        station_nvs_b = service.create_default_node_for_xml(
            self.xml.id, XmlNodeEnum.STATION, self.network_id
        )
        with db_transaction(self.db):
            self.db.query(XmlNodeInstModel) \
                .filter(XmlNodeInstModel.xml_id == self.xml.id) \
                .filter(XmlNodeInstModel.node_id == XmlNodeEnum.CHANNEL) \
                .filter(XmlNodeInstModel.parent_id == station_nvs_b) \
                .delete(synchronize_session=False)
        self._set_code(station_nvs_b, 'NVS')
        self._set_attr(station_nvs_b, XmlNodeAttrEnum.LATITUDE, 50.0)
        self._set_attr(station_nvs_b, XmlNodeAttrEnum.LONGITUDE, 80.0)
        self._set_dates(station_nvs_b, datetime(2022, 1, 1), None)

        channel_b = service.create_default_node_for_xml(
            self.xml.id, XmlNodeEnum.CHANNEL, self.station_a
        )
        self._set_code(channel_b, 'EHZ')
        self._set_attr(channel_b, XmlNodeAttrEnum.LOCATION_CODE, '00')
        self._set_attr(channel_b, XmlNodeAttrEnum.LATITUDE, 50.01)
        self._set_attr(channel_b, XmlNodeAttrEnum.LONGITUDE, 80.01)
        self._set_dates(channel_b, datetime(2022, 6, 1), None)

        # Epoch filter keeps only the 2020 marker, but periods still list both.
        payload = service.load_map(
            self.xml.id, 0, datetime(2020, 6, 1), include_channels=True
        )
        nvs = next(row for row in payload['stations'] if row['label'] == 'AN.NVS')
        self.assertEqual(
            nvs['epochs'],
            [
                {'start': datetime(2020, 1, 1), 'end': datetime(2021, 1, 1)},
                {'start': datetime(2022, 1, 1), 'end': None},
            ],
        )
        channel = next(row for row in payload['channels'] if row['label'] == 'AN.NVS.00.EHZ')
        self.assertEqual(
            channel['epochs'],
            [
                {'start': datetime(2020, 1, 1), 'end': datetime(2021, 1, 1)},
                {'start': datetime(2022, 6, 1), 'end': None},
            ],
        )

    def test_channels_omitted_until_requested(self):
        payload = NodeService(self).load_map(self.xml.id, 0, None)
        self.assertEqual(payload['channels'], [])
        self.assertEqual(len(payload['stations']), 2)
        full = NodeService(self).load_map(self.xml.id, 0, None, include_channels=True)
        self.assertEqual(full['channels'][0]['label'], 'AN.NVS.00.EHZ')

    def test_station_extent_is_network_aperture(self):
        payload = NodeService(self).load_map(self.xml.id, self.station_a, None)
        extent = payload['extent']
        self.assertGreater(extent['north'] - extent['south'], 1)
        self.assertGreater(extent['east'] - extent['west'], 1)
        self.assertLess(extent['south'], 50.0)
        self.assertGreater(extent['north'], 52.0)
        self.assertLess(extent['west'], 80.0)
        self.assertGreater(extent['east'], 84.0)

    def test_antimeridian_extent_is_the_short_arc(self):
        extent = padded_extent([(0.0, 170.0), (0.0, -170.0)])
        self.assertLess(extent['east'] - extent['west'], 40)

    def test_channel_orientation_qc_flags(self):
        # Default channel nodes omit azimuth/dip attribute rows.
        payload = NodeService(self).load_map(
            self.xml.id, 0, None, include_channels=True
        )
        channel = payload['channels'][0]
        self.assertIsNone(channel.get('azimuth'))
        self.assertIsNone(channel.get('dip'))
        self.assertIn('missing_azimuth', channel['qc'])
        self.assertIn('missing_dip', channel['qc'])

        self._ensure_attr(self.channel_a, XmlNodeAttrEnum.AZIMUTH, 90.0)
        self._ensure_attr(self.channel_a, XmlNodeAttrEnum.DIP, -90.0)
        payload = NodeService(self).load_map(
            self.xml.id, 0, None, include_channels=True
        )
        channel = payload['channels'][0]
        self.assertEqual(channel['azimuth'], 90.0)
        self.assertEqual(channel['dip'], -90.0)
        self.assertEqual(channel['qc'], [])

    def _ensure_attr(self, node_id, name, value):
        with db_transaction(self.db):
            row = self.db.query(XmlNodeAttrValModel) \
                .join(XmlNodeAttrValModel.attr) \
                .options(joinedload(XmlNodeAttrValModel.attr)) \
                .filter(XmlNodeAttrValModel.node_inst_id == node_id) \
                .filter(XmlNodeAttrModel.name == name) \
                .first()
            if row is None:
                attr = self.db.query(XmlNodeAttrModel) \
                    .filter(XmlNodeAttrModel.name == name) \
                    .first()
                self.assertIsNotNone(attr, name)
                row = XmlNodeAttrValModel(node_inst_id=node_id, attr_id=attr.id)
                self.db.add(row)
                self.db.flush()
            row.value_obj = value

    def _set_code(self, node_id, code):
        self._set_attr(node_id, XmlNodeAttrEnum.CODE, code)
        with db_transaction(self.db):
            node = self.db.get(XmlNodeInstModel, node_id)
            node.code = code

    def _set_attr(self, node_id, name, value):
        with db_transaction(self.db):
            row = self.db.query(XmlNodeAttrValModel) \
                .join(XmlNodeAttrValModel.attr) \
                .options(joinedload(XmlNodeAttrValModel.attr)) \
                .filter(XmlNodeAttrValModel.node_inst_id == node_id) \
                .filter(XmlNodeAttrModel.name == name) \
                .first()
            self.assertIsNotNone(row, name)
            row.value_obj = value

    def _set_dates(self, node_id, start, end):
        with db_transaction(self.db):
            node = self.db.get(XmlNodeInstModel, node_id)
            node.start_date = start
            node.end_date = end

    @classmethod
    def tearDownClass(cls):
        try:
            remove_db(cls.__name__)
        except OSError:
            pass

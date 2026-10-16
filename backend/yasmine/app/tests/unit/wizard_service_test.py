# 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
# WizardService and XmlService unit coverage without HTTP.

import unittest

from yasmine.app.enums.xml_node import XmlNodeEnum
from yasmine.app.models import XmlModel, XmlNodeInstModel
from yasmine.app.services.node_service import NodeService
from yasmine.app.services.wizard_service import WizardService
from tornado.web import HTTPError

from yasmine.app.services.xml_service import XmlService
from yasmine.app.tests.integration.utils.integration_util import migrate_db, remove_db
from yasmine.app.utils.db import db_transaction
from yasmine.app.utils.facade import ProcessMixin


class WizardXmlServiceTest(unittest.TestCase, ProcessMixin):

    @classmethod
    def setUpClass(cls):
        migrate_db(cls.__name__)

    def setUp(self):
        ProcessMixin.__init__(self)

    def _create_xml(self):
        xml = XmlModel(name='wizard-unit', source='t', module='m', uri='u', sender='s')
        with db_transaction(self.db):
            self.db.add(xml)
        self.db.refresh(xml)
        return xml

    def test_create_network_station_and_channel_info(self):
        xml = self._create_xml()
        wizard = WizardService(self)
        network_id = wizard.create_network(xml.id, 'XX', '2020-01-01T00:00:00', None)
        self.assertIsNotNone(network_id)
        station_info = wizard.get_station_info(network_id)
        self.assertEqual(station_info['start_date'], '2020-01-01T00:00:00')
        missing_station = wizard.get_station_info(999999)
        self.assertEqual(missing_station['start_date'], '')
        station_id = wizard.create_station(
            xml.id, 'TST', '2020-06-15T12:30:00', None, network_id, 1.5, 2.5, 10
        )
        self.assertIsNotNone(station_id)
        info = wizard.get_channel_info(station_id)
        self.assertEqual(info['latitude'], 1.5)
        self.assertEqual(info['longitude'], 2.5)
        self.assertEqual(info['elevation'], 10.0)
        self.assertEqual(info['start_date'], '2020-06-15T12:30:00')
        missing = wizard.get_channel_info(999999)
        self.assertEqual(missing['latitude'], 0)
        self.assertEqual(missing['start_date'], '')

    def test_node_service_default_network(self):
        xml = self._create_xml()
        node_id = NodeService(self).create_default_node_for_xml(xml.id, XmlNodeEnum.NETWORK, None)
        node = self.db.get(XmlNodeInstModel, node_id)
        self.assertIsNotNone(node)
        self.assertEqual(node.node_id, XmlNodeEnum.NETWORK)

    def test_node_service_delete_missing_is_noop(self):
        xml = self._create_xml()
        NodeService(self).delete_node_from_xml(xml.id, 999999)
        remaining = self.db.query(XmlNodeInstModel).filter(
            XmlNodeInstModel.xml_id == xml.id
        ).count()
        self.assertEqual(remaining, 0)

    def test_xml_service_validate_empty(self):
        xml = self._create_xml()
        try:
            result = XmlService(self).validate(xml.id)
            self.assertIsInstance(result, dict)
            self.assertIn('errors', result)
            self.assertIn('warnings', result)
        except HTTPError:
            pass

    def test_xml_service_missing_id(self):
        with self.assertRaises(HTTPError):
            XmlService(self).validate(999999)

    @classmethod
    def tearDownClass(cls):
        try:
            remove_db(cls.__name__)
        except OSError:
            pass

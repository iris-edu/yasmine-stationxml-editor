# 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
# Clone copies extension sidecars; export blocks on StationXML 1.2 XSD errors.

import io
import unittest
from unittest.mock import patch

from tornado.web import HTTPError

from yasmine.app.enums.xml_node import XmlNodeAttrEnum, XmlNodeEnum
from yasmine.app.models import XmlModel, XmlNodeInstModel
from yasmine.app.services.attribute_service import AttributeService
from yasmine.app.services.node_service import NodeService
from yasmine.app.tests.integration.utils.integration_util import (
    get_file_path,
    migrate_db,
    remove_db,
)
from yasmine.app.utils.db import db_transaction
from yasmine.app.utils.facade import ProcessMixin
from yasmine.app.utils.imp_exp import ExportStationXml, ImportStationXml


class NodeCloneSidecarAndExportGateTest(unittest.TestCase, ProcessMixin):

    @classmethod
    def setUpClass(cls):
        migrate_db(cls.__name__)

    def setUp(self):
        ProcessMixin.__init__(self)

    def _create_xml(self):
        xml = XmlModel(name='clone-sidecar', source='t', module='m', uri='u', sender='s')
        with db_transaction(self.db):
            self.db.add(xml)
        self.db.refresh(xml)
        return xml

    def test_water_level_enum_is_canonical(self):
        self.assertEqual(XmlNodeAttrEnum.WATER_LEVEL, 'water_level')
        self.assertIsNotNone(
            AttributeService._measured_value_class(XmlNodeAttrEnum.WATER_LEVEL)
        )

    def test_clone_copies_extension_sidecar(self):
        xml = self._create_xml()
        source_id = NodeService(self).create_default_node_for_xml(
            xml.id, XmlNodeEnum.NETWORK, None
        )
        sidecar = '{"elements":[{"qname":"{urn:yasmine:test}Extra"}]}'
        source = self.db.get(XmlNodeInstModel, source_id)
        with db_transaction(self.db):
            source.extension_sidecar = sidecar
        cloned_id = NodeService(self).add_node_to_xml(xml.id, source_id, None)
        cloned = self.db.get(XmlNodeInstModel, cloned_id)
        self.assertNotEqual(cloned.id, source_id)
        self.assertEqual(cloned.extension_sidecar, sidecar)

    def test_export_blocks_on_xsd_errors(self):
        path = get_file_path('stationxmls/compliance_minimal_v_1_2.xml')
        with open(path, 'rb') as handle:
            imported = ImportStationXml(
                'export-gate', io.BytesIO(handle.read()), self
            ).run()
        with patch(
            'yasmine.app.utils.imp_exp.validate_stationxml_12',
            return_value=[{
                'path': '/FDSNStationXML/Network',
                'message': 'test XSD failure',
            }],
        ):
            with self.assertRaises(HTTPError) as error:
                ExportStationXml(imported.id, self).run()
        self.assertEqual(error.exception.status_code, 400)
        self.assertIn('test XSD failure', error.exception.reason)

    @classmethod
    def tearDownClass(cls):
        try:
            remove_db(cls.__name__)
        except OSError:
            pass

# 2026-09-24, version 4.3.3-beta: ASGSR, Alexey Emanov
# User library exchange is StationXML and does not create an XML document.

import io
import os
import unittest

from yasmine.app.enums.xml_node import XmlNodeEnum
from yasmine.app.models import UserLibraryModel, XmlModel, XmlNodeInstModel
from yasmine.app.services.node_service import NodeService
from yasmine.app.tests.integration.utils.integration_util import (
    get_file_path,
    migrate_db,
    remove_db,
)
from yasmine.app.utils.db import db_transaction
from yasmine.app.utils.facade import ProcessMixin
from yasmine.app.utils.imp_exp import (
    ExportUserLibrary,
    ImportStationXml,
    ImportUserLibrary,
)
from yasmine.app.utils.stationxml_validation import STATIONXML_IMPORT_ERROR


class UserLibraryExchangeTest(unittest.TestCase, ProcessMixin):

    @classmethod
    def setUpClass(cls):
        migrate_db(cls.__name__)

    def setUp(self):
        ProcessMixin.__init__(self)

    def _import_fixture(self):
        path = get_file_path('stationxmls/compliance_minimal_v_1_2.xml')
        if not os.path.isfile(path):
            self.skipTest('fixture missing: %s' % path)
        with open(path, 'rb') as handle:
            return ImportStationXml('seed-xml', io.BytesIO(handle.read()), self).run()

    def _snapshot(self, library_id):
        nodes = self.db.query(XmlNodeInstModel).filter(
            XmlNodeInstModel.user_library_id == library_id
        ).order_by(XmlNodeInstModel.node_id, XmlNodeInstModel.code).all()
        rows = []
        for node in nodes:
            attrs = {}
            for attr in node.attr_vals:
                attrs[attr.attr_name] = attr.value_obj
            by_id = {node.id: node for node in nodes}
            parent = by_id.get(node.parent_id)
            rows.append({
                'node_id': node.node_id,
                'code': node.code,
                'parent': None if parent is None else (parent.node_id, parent.code),
                'xml_id': node.xml_id,
                'attrs': attrs,
            })
        return rows

    def test_export_import_keeps_codes_and_skips_xml_documents(self):
        xml = self._import_fixture()
        network = self.db.query(XmlNodeInstModel).filter(
            XmlNodeInstModel.xml_id == xml.id,
            XmlNodeInstModel.node_id == XmlNodeEnum.NETWORK,
        ).one()
        library = UserLibraryModel(name='exchange-lib')
        with db_transaction(self.db):
            self.db.add(library)
        self.db.refresh(library)
        NodeService(self).add_node_to_library(library.id, network.id)

        filename, payload = ExportUserLibrary(library.id, self).run()
        body = payload.getvalue()
        self.assertEqual(filename, 'exchange-lib.xml')
        self.assertIn(b'<FDSNStationXML', body)
        self.assertIn(b'schemaVersion="1.2"', body)
        self.assertIn(b'<Module>exchange-lib</Module>', body)

        xml_count = self.db.query(XmlModel).count()
        imported = ImportUserLibrary('', io.BytesIO(body), self).run()
        self.assertEqual(self.db.query(XmlModel).count(), xml_count)
        self.assertEqual(imported.name, 'exchange-lib (2)')
        placeholder = ImportUserLibrary(
            'Use the StationXML Module name', io.BytesIO(body), self
        ).run()
        self.assertEqual(placeholder.name, 'exchange-lib (3)')
        self.assertIsNone(
            self.db.query(XmlModel).filter(XmlModel.name == imported.name).first()
        )

        original = self._snapshot(library.id)
        copied = self._snapshot(imported.id)
        self.assertEqual(
            [(row['node_id'], row['code']) for row in original],
            [(row['node_id'], row['code']) for row in copied],
        )
        self.assertEqual(
            {row['code'] for row in copied},
            {'XX', 'AAA', 'BHZ'},
        )
        for source, target in zip(original, copied):
            self.assertIsNone(target['xml_id'])
            self.assertEqual(target['parent'], source['parent'])
            for name, value in source['attrs'].items():
                self.assertIn(name, target['attrs'])
                self.assertEqual(target['attrs'][name], value, name)

    def test_root_station_and_channel_are_not_placed_in_a_network(self):
        library = UserLibraryModel(name='mixed-lib')
        with db_transaction(self.db):
            self.db.add(library)
        self.db.refresh(library)
        service = NodeService(self)
        network_id = service.create_default_node_for_library(
            library.id, XmlNodeEnum.NETWORK, None
        )
        nested_station_id = service.create_default_node_for_library(
            library.id, XmlNodeEnum.STATION, network_id
        )
        service.create_default_node_for_library(
            library.id, XmlNodeEnum.CHANNEL, nested_station_id
        )
        root_station_id = service.create_default_node_for_library(
            library.id, XmlNodeEnum.STATION, None
        )
        service.create_default_node_for_library(
            library.id, XmlNodeEnum.CHANNEL, root_station_id
        )
        service.create_default_node_for_library(
            library.id, XmlNodeEnum.CHANNEL, None
        )
        self._set_code(network_id, 'DD')
        self._set_code(nested_station_id, 'NEST')
        self._set_code(root_station_id, 'ROOT')

        _, payload = ExportUserLibrary(library.id, self).run()
        imported = ImportUserLibrary('', io.BytesIO(payload.getvalue()), self).run()
        original = self._shape(library.id)
        copied = self._shape(imported.id)
        self.assertEqual(copied, original)
        self.assertIn((XmlNodeEnum.STATION, 'ROOT', None), copied)
        self.assertIn((XmlNodeEnum.NETWORK, 'DD', None), copied)
        channel_parents = [parent for node_id, _code, parent in copied if node_id == XmlNodeEnum.CHANNEL]
        self.assertTrue(channel_parents)
        self.assertTrue(all(parent is None or parent[0] == XmlNodeEnum.STATION for parent in channel_parents))
        station_parents = [parent for node_id, _code, parent in copied if node_id == XmlNodeEnum.STATION]
        self.assertIn(None, station_parents)
        self.assertIn((XmlNodeEnum.NETWORK, 'DD'), station_parents)

    def _shape(self, library_id):
        return [
            (row['node_id'], row['code'], row['parent'])
            for row in self._snapshot(library_id)
        ]

    def _set_code(self, node_id, code):
        from yasmine.app.models import XmlNodeAttrModel, XmlNodeAttrValModel
        with db_transaction(self.db):
            node = self.db.get(XmlNodeInstModel, node_id)
            node.code = code
            attr = self.db.query(XmlNodeAttrValModel).join(
                XmlNodeAttrValModel.attr
            ).filter(
                XmlNodeAttrValModel.node_inst_id == node_id,
                XmlNodeAttrModel.name == 'code',
            ).first()
            if attr is not None:
                attr.value_obj = code

    def test_non_stationxml_is_rejected(self):
        before = self.db.query(UserLibraryModel).count()
        with self.assertRaises(ValueError) as error:
            ImportUserLibrary('nope', io.BytesIO(b'not xml'), self).run()
        self.assertEqual(str(error.exception), STATIONXML_IMPORT_ERROR)
        self.assertEqual(self.db.query(UserLibraryModel).count(), before)

        foreign = b'''<?xml version="1.0"?>
        <seiscomp xmlns="http://geofon.gfz-potsdam.de/ns/seiscomp3-schema/0.11">
          <Inventory></Inventory>
        </seiscomp>'''
        with self.assertRaises(ValueError):
            ImportUserLibrary('nope', io.BytesIO(foreign), self).run()
        self.assertEqual(self.db.query(UserLibraryModel).count(), before)

    def tearDown(self):
        with db_transaction(self.db):
            self.db.query(XmlModel).delete()
            self.db.query(UserLibraryModel).delete()

    @classmethod
    def tearDownClass(cls):
        try:
            remove_db(cls.__name__)
        except OSError:
            pass

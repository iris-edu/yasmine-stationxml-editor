# 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
# Tree loads return rows and do not re-execute the node query.

import unittest

from sqlalchemy import event

from yasmine.app.enums.xml_node import XmlNodeEnum
from yasmine.app.models import UserLibraryModel, XmlModel
from yasmine.app.services.node_service import NodeService
from yasmine.app.tests.integration.utils.integration_util import migrate_db, remove_db
from yasmine.app.utils.db import db_transaction
from yasmine.app.utils.facade import ProcessMixin


class NodeLoadTest(unittest.TestCase, ProcessMixin):

    @classmethod
    def setUpClass(cls):
        migrate_db(cls.__name__)

    def setUp(self):
        ProcessMixin.__init__(self)

    def _count_queries(self, func):
        bind = self.db.get_bind()
        state = {'n': 0}

        def _before(*_args, **_kwargs):
            state['n'] += 1

        event.listen(bind, 'before_cursor_execute', _before)
        try:
            result = func()
        finally:
            event.remove(bind, 'before_cursor_execute', _before)
        return result, state['n']

    def test_load_library_root_networks(self):
        library = UserLibraryModel(name='load-lib')
        with db_transaction(self.db):
            self.db.add(library)
        self.db.refresh(library)
        node_id = NodeService(self).create_default_node_for_library(
            library.id, XmlNodeEnum.NETWORK, None
        )
        rows = NodeService(self).load_node_from_library(
            library.id, XmlNodeEnum.NETWORK, '0'
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['id'], node_id)
        self.assertEqual(
            NodeService(self).load_node_from_library(9999, XmlNodeEnum.NETWORK, '0'),
            [],
        )

    def test_load_xml_runs_node_query_once(self):
        xml = XmlModel(name='load-xml', source='t', module='m', uri='u', sender='s')
        with db_transaction(self.db):
            self.db.add(xml)
        self.db.refresh(xml)
        NodeService(self).create_default_node_for_xml(
            xml.id, XmlNodeEnum.NETWORK, None
        )
        rows, query_count = self._count_queries(
            lambda: NodeService(self).load_node_from_xml(xml.id, 0, [])
        )
        self.assertEqual(len(rows), 1)
        self.assertLessEqual(query_count, 4)
        self.assertEqual(
            NodeService(self).load_node_from_xml(xml.id, 9999, []),
            [],
        )

    @classmethod
    def tearDownClass(cls):
        try:
            remove_db(cls.__name__)
        except OSError:
            pass

# 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
# db_transaction commits on success and rolls back on error.

import unittest

from yasmine.app.models import ConfigModel
from yasmine.app.tests.integration.utils.integration_util import migrate_db, remove_db
from yasmine.app.utils.db import db_transaction
from yasmine.app.utils.facade import ProcessMixin


class DbTransactionTest(unittest.TestCase, ProcessMixin):

    @classmethod
    def setUpClass(cls):
        migrate_db(cls.__name__)

    def setUp(self):
        ProcessMixin.__init__(self)

    def test_rollback_on_exception(self):
        marker = 'tx-rollback-marker'
        try:
            with db_transaction(self.db):
                record = ConfigModel(group='test', name=marker)
                record.value_obj = '1'
                self.db.add(record)
                raise RuntimeError('force rollback')
        except RuntimeError:
            pass
        found = self.db.query(ConfigModel).filter(
            ConfigModel.group == 'test', ConfigModel.name == marker
        ).first()
        self.assertIsNone(found)

    def test_explicit_rollback_before_success_false_does_not_persist(self):
        marker = 'tx-explicit-rollback'
        with db_transaction(self.db):
            record = ConfigModel(group='test', name=marker)
            record.value_obj = '1'
            self.db.add(record)
            self.db.flush()
            self.db.rollback()
        found = self.db.query(ConfigModel).filter(
            ConfigModel.group == 'test', ConfigModel.name == marker
        ).first()
        self.assertIsNone(found)

    def test_commit_on_success(self):
        marker = 'tx-commit-marker'
        with db_transaction(self.db):
            record = ConfigModel(group='test', name=marker)
            record.value_obj = '1'
            self.db.add(record)
        found = self.db.query(ConfigModel).filter(
            ConfigModel.group == 'test', ConfigModel.name == marker
        ).first()
        self.assertIsNotNone(found)

    @classmethod
    def tearDownClass(cls):
        try:
            remove_db(cls.__name__)
        except OSError:
            pass

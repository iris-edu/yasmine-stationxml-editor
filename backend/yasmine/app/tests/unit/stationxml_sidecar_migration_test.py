# 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
# Additive sidecar migration from the previous Alembic head.

import os
import unittest

from sqlalchemy import create_engine, inspect, text

from yasmine.app.settings import TMP_ROOT
from yasmine.app.utils.db import syncdb


PREVIOUS_HEAD = 'd4e5f6a7b8c9'
SIDECAR_REVISION = 'e5f6a7b8c9d0'


class StationXmlSidecarMigrationTest(unittest.TestCase):

    def test_upgrade_from_previous_head_adds_sidecar_columns(self):
        import yasmine.app.settings as settings

        db_file = os.path.join(TMP_ROOT, 'sidecar_migration.sqlite')
        if os.path.exists(db_file):
            os.remove(db_file)
        previous = settings.DB_CONNECTION
        cwd = os.getcwd()
        try:
            settings.DB_CONNECTION = 'sqlite:///%s' % db_file
            syncdb(argv=['--raiseerr', 'upgrade', PREVIOUS_HEAD])
            engine = create_engine(settings.DB_CONNECTION)
            try:
                inspector = inspect(engine)
                self.assertNotIn(
                    'extension_sidecar',
                    [column['name'] for column in inspector.get_columns('xml')],
                )
                self.assertNotIn(
                    'extension_sidecar',
                    [
                        column['name']
                        for column in inspector.get_columns('xml_node_instance')
                    ],
                )
            finally:
                engine.dispose()

            syncdb(argv=['--raiseerr', 'upgrade', SIDECAR_REVISION])
            engine = create_engine(settings.DB_CONNECTION)
            try:
                inspector = inspect(engine)
                self.assertIn(
                    'extension_sidecar',
                    [column['name'] for column in inspector.get_columns('xml')],
                )
                self.assertIn(
                    'extension_sidecar',
                    [
                        column['name']
                        for column in inspector.get_columns('xml_node_instance')
                    ],
                )
                with engine.connect() as connection:
                    names = [
                        row[0]
                        for row in connection.execute(
                            text('SELECT name FROM xml_node_attribute')
                        )
                    ]
                self.assertIn('data_availability', names)
            finally:
                engine.dispose()
        finally:
            settings.DB_CONNECTION = previous
            os.chdir(cwd)
            if os.path.exists(db_file):
                os.remove(db_file)

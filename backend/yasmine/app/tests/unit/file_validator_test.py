# 2026-09-18, version 4.1.3-beta: ASGSR, Alexey Emanov
# FileValidatorService missing-schema behavior.

import os
import tempfile
import unittest

from yasmine.app.services.file_validator_service import FileValidatorService
from yasmine.app.settings import RESOURCES_SCHEMA_AROL


class FileValidatorServiceTest(unittest.TestCase):

    def test_missing_schema_raises(self):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        tmp.write(b'[]')
        tmp.close()
        try:
            with self.assertRaises(Exception):
                FileValidatorService().validate([tmp.name], '/no/such/schema.json')
        finally:
            os.unlink(tmp.name)

    def test_invalid_json_is_an_error(self):
        schema = os.path.join(RESOURCES_SCHEMA_AROL, 'key.schema.json')
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        tmp.write(b'{"start_time": ')
        tmp.close()
        try:
            errors = FileValidatorService().validate([tmp.name], schema)
        finally:
            os.unlink(tmp.name)
        self.assertEqual(len(errors), 1)
        self.assertIn('invalid JSON', errors[0])

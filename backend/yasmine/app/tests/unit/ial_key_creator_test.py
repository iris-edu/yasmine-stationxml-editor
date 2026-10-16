# 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
# AROL key scanner: missing folders and incomplete JSON must not crash.

import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from yasmine.app.helpers.ial.ial_key_creator import IalKeyCreator
from yasmine.app.services.file_convertor_service import FileConvertorService
from yasmine.app.services.file_validator_service import FileValidatorService


class IalKeyCreatorTest(unittest.TestCase):

    def test_missing_library_folder_is_empty(self):
        sensors, dataloggers = IalKeyCreator().create_keys('/no/such/arol/objects')
        self.assertEqual(sensors, {'filters': [], 'responses': []})
        self.assertEqual(dataloggers, {'filters': [], 'responses': []})

    def test_find_all_key_files_skips_missing_dir(self):
        self.assertEqual(IalKeyCreator._find_all_key_files('/no/such/dir'), [])

    @patch.object(FileValidatorService, 'validate', return_value=[])
    def test_missing_filters_and_responses_are_empty(self, _validate):
        root = tempfile.mkdtemp()
        try:
            vendor = os.path.join(root, 'Vendor')
            os.makedirs(vendor)
            with open(os.path.join(vendor, 'Vendor.json'), 'w') as handle:
                json.dump({}, handle)
            result = IalKeyCreator()._create(root)
            self.assertEqual(result['filters'], [])
            self.assertEqual(result['responses'], [])
        finally:
            os.remove(os.path.join(vendor, 'Vendor.json'))
            os.rmdir(vendor)
            os.rmdir(root)

    @patch.object(FileValidatorService, 'validate', return_value=[])
    def test_null_applicable_filters_are_filled(self, _validate):
        root = tempfile.mkdtemp()
        try:
            vendor = os.path.join(root, 'Vendor')
            os.makedirs(vendor)
            with open(os.path.join(vendor, 'Vendor.json'), 'w') as handle:
                json.dump({
                    'filters': [{'code': 'gain'}],
                    'responses': [{'name': 'default', 'applicable_filters': None}],
                }, handle)
            result = IalKeyCreator()._create(root)
            self.assertEqual(result['filters'][0]['code'], 'gain')
            self.assertIn('gain', result['responses'][0]['applicable_filters'])
        finally:
            os.remove(os.path.join(vendor, 'Vendor.json'))
            os.rmdir(vendor)
            os.rmdir(root)

    def test_yaml_dates_are_kept_and_bad_json_is_skipped(self):
        src = tempfile.mkdtemp()
        converted = None
        try:
            vendor = os.path.join(src, 'guralp')
            os.makedirs(vendor)
            with open(os.path.join(vendor, 'guralp.yaml'), 'w') as handle:
                handle.write(
                    'mandatory_filters: [sensors_manufacturer, sensors_model]\n'
                    'filters:\n'
                    '  - name: Sensors manufacturer\n'
                    '    code: sensors_manufacturer\n'
                    '    help: Select the manufacturer\n'
                    '  - name: Sensors model\n'
                    '    code: sensors_model\n'
                    '    help: Select the model\n'
                    '  - name: Start time\n'
                    '    code: start_time\n'
                    '    help: Select the start date\n'
                    'responses:\n'
                    '  - path: guralp/CMG40T.response.yaml\n'
                    '    applicable_filters:\n'
                    '      sensors_manufacturer: Guralp\n'
                    '      sensors_model: CMG40T\n'
                    '      start_time: 1995-06-27\n'
                    '      end_time: 2005-06-07\n'
                )
            converted = FileConvertorService().convert_from_folder(src)
            bad = os.path.join(converted, 'broken')
            os.makedirs(bad)
            with open(os.path.join(bad, 'broken.json'), 'w') as handle:
                handle.write('{"start_time": ')
            result = IalKeyCreator()._create(converted)
        finally:
            shutil.rmtree(src)
            if converted:
                shutil.rmtree(converted)
        self.assertEqual(len(result['responses']), 1)
        filters = result['responses'][0]['applicable_filters']
        self.assertEqual(filters['start_time'], '1995-06-27')
        self.assertEqual(filters['end_time'], '2005-06-07')
        self.assertEqual(filters['sensors_manufacturer'], 'Guralp')

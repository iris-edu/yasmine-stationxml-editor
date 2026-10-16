# 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tornado.web import HTTPError

from yasmine.app.services.stationxml_help_service import (
    StationXmlHelpService,
    clear_stationxml_help_cache,
)


RESOURCE_DIR = (
    Path(__file__).resolve().parents[3]
    / 'resources'
    / 'schemas'
    / 'stationxml'
    / '1.2'
)


class StationXmlHelpServiceTest(unittest.TestCase):

    def tearDown(self):
        clear_stationxml_help_cache()

    def test_entry_payload_contains_breadcrumbs(self):
        path = '/FDSNStationXML/Network/Station/Channel/@code'
        payload = StationXmlHelpService().entry_payload(path)
        self.assertEqual(payload['entry']['xmlName'], 'code')
        self.assertEqual(payload['breadcrumbs'][-1]['path'], path)
        self.assertEqual(
            [item['xmlName'] for item in payload['breadcrumbs'][:4]],
            ['FDSNStationXML', 'Network', 'Station', 'Channel'],
        )

    def test_unknown_path_is_404(self):
        with self.assertRaises(HTTPError) as error:
            StationXmlHelpService().entry('/not/in/stationxml')
        self.assertEqual(error.exception.status_code, 404)

    def test_catalog_copy_cannot_mutate_cached_catalog(self):
        service = StationXmlHelpService()
        copied = service.catalog_copy()
        copied['metadata']['schemaVersion'] = 'changed'
        self.assertEqual(
            service.catalog()['metadata']['schemaVersion'],
            '1.2',
        )

    def test_catalog_is_loaded_once(self):
        service = StationXmlHelpService()
        first = service.catalog()
        second = service.catalog()
        self.assertIs(first, second)
        self.assertEqual(service.etag(), service.etag())

    def test_corrupt_catalog_is_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'catalog.json'
            path.write_text(json.dumps({
                'metadata': {'schemaVersion': '1.2', 'entryCount': 2},
                'nodes': {},
            }), encoding='utf-8')
            with patch(
                'yasmine.app.services.stationxml_help_service.'
                'stationxml_help_catalog_path',
                return_value=path,
            ):
                clear_stationxml_help_cache()
                with self.assertRaises(ValueError):
                    StationXmlHelpService().catalog()

    def test_committed_catalog_is_utf8(self):
        raw = (RESOURCE_DIR / 'catalog.json').read_bytes()
        decoded = raw.decode('utf-8')
        self.assertIn('StationXML', decoded)


if __name__ == '__main__':
    unittest.main()

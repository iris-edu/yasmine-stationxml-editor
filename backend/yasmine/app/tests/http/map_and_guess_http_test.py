# 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
# Map payload, tile bounds, and wizard code-guess endpoints.

from yasmine.app.enums.xml_node import XmlNodeEnum
from yasmine.app.tests.common.http import YasmineHTTPTestCase


class MapAndGuessHttpTest(YasmineHTTPTestCase):

    def _create_xml(self):
        response, payload = self.fetch_json('/api/xml/', method='POST', body={
            'id': -1,
            'name': 'map-guess-xml',
            'source': 'test',
            'module': 'yasmine-test',
            'uri': 'http://example.test',
            'sender': 'tester',
            'created_at': '2026-09-22T02:14:25',
        })
        self.assertEqual(response.code, 200, msg=getattr(response, 'body', b''))
        return payload['data']['id']

    def test_map_empty_inventory_and_errors(self):
        xml_id = self._create_xml()
        response, payload = self.fetch_json('/api/xml/map/%s/' % xml_id)
        self.assertEqual(response.code, 200)
        self.assertTrue(payload.get('success'))
        self.assertEqual(payload['data']['stations'], [])
        self.assertEqual(payload['data']['channels'], [])
        self.assertIsNone(payload['data']['extent'])

        response, payload = self.fetch_json('/api/xml/map/%s/?epoch=not-a-date' % xml_id)
        self.assertEqual(response.code, 200)
        self.assertFalse(payload.get('success'))

        response, payload = self.fetch_json('/api/xml/map/%s/?nodeId=999999' % xml_id)
        self.assertEqual(response.code, 200)
        self.assertFalse(payload.get('success'))

        response, payload = self.fetch_json('/api/xml/map/%s/?nodeId=abc' % xml_id)
        self.assertEqual(response.code, 200)
        self.assertFalse(payload.get('success'))

        response, payload = self.fetch_json('/api/xml/node-path/?nodeId=abc')
        self.assertEqual(response.code, 200)
        self.assertFalse(payload.get('success'))

        response, payload = self.fetch_json('/api/xml/similar-channel/?xmlId=abc&nodeInstanceId=1')
        self.assertEqual(response.code, 200)
        self.assertFalse(payload.get('success'))

        response, payload = self.fetch_json('/api/xml/tree/%s/' % xml_id, method='POST', body={
            'node_inst_id': 999999,
            'parentId': None,
            'nodeType': XmlNodeEnum.NETWORK,
        })
        self.assertEqual(response.code, 200)
        self.assertFalse(payload.get('success'))

        response, payload = self.fetch_json('/api/xml/attr/999999', method='DELETE')
        self.assertEqual(response.code, 200)
        self.assertFalse(payload.get('success'))

        response, payload = self.fetch_json('/api/xml/tree/%s/' % xml_id, method='POST', body={
            'node_inst_id': 0,
            'parentId': None,
            'nodeType': XmlNodeEnum.NETWORK,
        })
        network_id = payload['data']['nodeId']
        response, payload = self.fetch_json(
            '/api/xml/map/%s/?nodeId=%s' % (xml_id, network_id)
        )
        self.assertEqual(response.code, 200)
        self.assertTrue(payload.get('success'))

    def test_gzip_transform_is_enabled(self):
        from tornado.web import GZipContentEncoding
        self.assertIn(GZipContentEncoding, self._app.transforms)

    def test_cached_tile_is_served_without_upstream(self):
        import os
        import tempfile
        from unittest.mock import patch
        from yasmine.app.handlers import xml_bldr
        cache = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__('shutil').rmtree(cache, ignore_errors=True))
        path = os.path.join(cache, 'cached.png')
        payload = b'\x89PNG\r\n\x1a\ncached-tile'
        with open(path, 'wb') as handle:
            handle.write(payload)
        with patch.object(xml_bldr, 'tile_cache_path', return_value=path):
            response = self.fetch('/api/map/tiles/osm/1/0/0')
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, payload)
        self.assertIn('image/png', response.headers.get('Content-Type', ''))

    def test_tile_out_of_range_is_400(self):
        response, payload = self.fetch_json('/api/map/tiles/osm/99/0/0')
        self.assertEqual(response.code, 400)
        self.assertFalse(payload.get('success'))
        response, payload = self.fetch_json('/api/map/tiles/osm/1/8/0')
        self.assertEqual(response.code, 400)

    def test_guess_soh_and_prefix(self):
        response, payload = self.fetch_json('/api/wizard/guess/soh-code/', method='POST', body={
            'channelDescription': 'Temperature',
            'sampleRate': '0.1 Hz',
        })
        self.assertEqual(response.code, 200)
        self.assertEqual(payload.get('code'), 'VKI')
        self.assertAlmostEqual(payload.get('sampleRate'), 0.1)

        response, payload = self.fetch_json('/api/wizard/guess/prefix/', method='POST', body={
            'sensorType': 'groundVel',
            'angularPeriod': '120 s',
            'sampleRate': '100 Hz',
        })
        self.assertEqual(response.code, 200)
        self.assertEqual(payload.get('prefix'), 'HH')

        response = self.fetch(
            '/api/wizard/guess/code/',
            method='POST',
            body='{"libraryType":"unknown","sensorKeys":[],"dataloggerKeys":[]}',
            headers={'Content-Type': 'application/json'},
        )
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body.decode('utf-8'), '')

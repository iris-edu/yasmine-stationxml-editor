# 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
from urllib.parse import quote

from yasmine.app.tests.common.http import YasmineHTTPTestCase


class StationXmlHelpApiTest(YasmineHTTPTestCase):

    def test_catalog_contract(self):
        response, payload = self.fetch_json('/api/stationxml/help/1.2/')
        self.assertEqual(response.code, 200)
        self.assertEqual(payload['metadata']['schemaVersion'], '1.2')
        self.assertEqual(payload['metadata']['entryCount'], 482)
        self.assertEqual(payload['rootPath'], '/FDSNStationXML')
        self.assertIn('ETag', response.headers)
        self.assertIn('immutable', response.headers.get('Cache-Control', ''))

    def test_entry_lookup_contract(self):
        path = '/FDSNStationXML/Network/Station/Channel/@code'
        response, payload = self.fetch_json(
            '/api/stationxml/help/1.2/?path=%s' % quote(path)
        )
        self.assertEqual(response.code, 200)
        self.assertEqual(payload['entry']['xmlName'], 'code')
        self.assertEqual(payload['entry']['path'], path)
        self.assertTrue(payload['breadcrumbs'])

    def test_unknown_path_is_json_404(self):
        response, payload = self.fetch_json(
            '/api/stationxml/help/1.2/?path=%s'
            % quote('/not/in/stationxml')
        )
        self.assertEqual(response.code, 404)
        self.assertFalse(payload.get('success', True))

    def test_legacy_help_endpoint_is_unchanged(self):
        response, payload = self.fetch_json('/api/help/xml_list/')
        self.assertEqual(response.code, 200)
        self.assertIn('content', payload)
        self.assertIn('Export', payload['content'])
        self.assertIn('StationXML', payload['content'])

    def test_node_navigation_help_describes_the_inventory_tree(self):
        response, payload = self.fetch_json('/api/help/children/')
        self.assertEqual(response.code, 200)
        content = payload.get('content') or ''
        self.assertIn('Inventory', content)
        self.assertIn('Epoch', content)
        self.assertIn('wizard', content.lower())
        self.assertGreater(len(content), 400)

    def test_settings_help_describes_nrl_and_required_fields(self):
        response, payload = self.fetch_json('/api/help/settings/')
        self.assertEqual(response.code, 200)
        content = payload.get('content') or ''
        self.assertIn('NRL', content)
        self.assertIn('Required Fields', content)

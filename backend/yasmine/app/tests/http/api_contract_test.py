# 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
# Grid LIKE pattern and JSON API error envelope.

import json
from urllib.parse import quote
import unittest

from yasmine.app.tests.common.http import YasmineHTTPTestCase


class ApiContractTest(YasmineHTTPTestCase):

    def test_healthz(self):
        response, payload = self.fetch_json('/healthz')
        self.assertEqual(response.code, 200)
        self.assertTrue(payload.get('success'))
        self.assertEqual(payload.get('status'), 'ok')
        trailing, trailing_payload = self.fetch_json('/healthz/')
        self.assertEqual(trailing.code, 200)
        self.assertEqual(trailing_payload.get('status'), 'ok')

    def test_build_info(self):
        response, payload = self.fetch_json('/api/build/')
        self.assertEqual(response.code, 200)
        self.assertTrue(payload.get('success'))
        data = payload.get('data') or {}
        self.assertIn('build_timestamp', data)
        self.assertIn('commit_revision', data)
        plain, plain_payload = self.fetch_json('/api/build')
        self.assertEqual(plain.code, 200)
        self.assertEqual(
            (plain_payload.get('data') or {}).get('commit_revision'),
            data.get('commit_revision'),
        )

    def test_xml_list_envelope(self):
        response, payload = self.fetch_json('/api/xml/')
        self.assertEqual(response.code, 200)
        self.assertIsInstance(payload, dict)
        self.assertTrue(payload.get('success'))
        self.assertIn('data', payload)

    def test_config_get_envelope(self):
        response, payload = self.fetch_json('/api/cfg/0')
        self.assertEqual(response.code, 200)
        self.assertIsInstance(payload, dict)
        self.assertIn('general__source', payload)

    def test_unknown_api_path_returns_json(self):
        response, payload = self.fetch_json('/api/does-not-exist/')
        self.assertIn(response.code, (403, 404, 405, 500))
        content_type = response.headers.get('Content-Type', '')
        self.assertIn('json', content_type.lower())
        self.assertIsInstance(payload, dict)
        self.assertFalse(payload.get('success', True))

    def test_config_put_without_separator_is_json_error(self):
        response, payload = self.fetch_json(
            '/api/cfg/0',
            method='PUT',
            body={'id': 0, 'badkey': 'x'},
        )
        self.assertIn(response.code, (200, 400, 500))
        self.assertIsInstance(payload, dict)
        if response.code == 200:
            self.assertFalse(payload.get('success', True))
        else:
            self.assertFalse(payload.get('success', True))

    def test_empty_put_body_does_not_500_html(self):
        response = self.fetch('/api/cfg/0', method='PUT', body='', headers={
            'Content-Type': 'application/json',
        })
        content_type = response.headers.get('Content-Type', '')
        if response.code >= 400:
            self.assertIn('json', content_type.lower())

    def test_xml_list_any_match_filter_does_not_500(self):
        filt = json.dumps([{
            'property': 'name',
            'value': 'no-such-xml',
            'anyMatch': True,
            'caseSensitive': True,
        }])
        response, payload = self.fetch_json('/api/xml/?filter=%s' % quote(filt))
        self.assertEqual(response.code, 200, msg=getattr(response, 'body', b''))
        self.assertTrue(payload.get('success'))

    def test_help_known_key(self):
        response, payload = self.fetch_json('/api/help/xml_list/')
        self.assertEqual(response.code, 200)
        self.assertIn('content', payload)

    def test_nrlv2_health_rejects_file_url(self):
        response, payload = self.fetch_json('/api/nrlv2/health?url=file:///etc/passwd')
        self.assertEqual(response.code, 200)
        self.assertFalse(payload.get('success', True))

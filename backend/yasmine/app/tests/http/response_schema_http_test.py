# 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
# HTTP contract tests for the StationXML 1.2 Response descriptor.

from yasmine.app.tests.common.http import YasmineHTTPTestCase
from yasmine.app.tests.unit.response_tree_schema_test import (
    _container,
    _filter_branches,
    _polynomial,
    _response,
    _sensitivity,
    _stage,
)


class ResponseSchemaHttpTest(YasmineHTTPTestCase):

    def test_schema_endpoint_is_cacheable_and_complete(self):
        response, payload = self.fetch_json('/api/channel/response/schema/')
        self.assertEqual(response.code, 200)
        self.assertTrue(payload['success'])
        self.assertEqual(payload['data']['schemaVersion'], '1.2')
        self.assertIn('PolesZeros', payload['data']['types'])
        self.assertIn('max-age=', response.headers.get('Cache-Control', ''))
        self.assertTrue(response.headers.get('ETag'))

        no_slash, no_slash_payload = self.fetch_json('/api/channel/response/schema')
        self.assertEqual(no_slash.code, 200)
        self.assertEqual(no_slash_payload['data']['id'], payload['data']['id'])

    def test_validation_accepts_empty_legacy_response(self):
        response, payload = self.fetch_json(
            '/api/channel/response/validate/',
            method='POST',
            body={'response': {'Response': {'attributes': {'resourceId': 'empty'}}}},
        )
        self.assertEqual(response.code, 200)
        self.assertTrue(payload['success'])
        self.assertTrue(payload['valid'])
        self.assertEqual(payload['issues'], [])
        self.assertEqual(payload['data'], payload['issues'])

    def test_validation_accepts_every_response_branch(self):
        payloads = {
            'InstrumentSensitivity': _response([_sensitivity()]),
            'InstrumentPolynomial': _response([_polynomial('InstrumentPolynomial')]),
            'PolynomialStage': _response([
                _polynomial('InstrumentPolynomial'),
                _container('Stage', [_polynomial()], attributes={'number': '1'}),
            ]),
        }
        payloads.update({
            name: _response([_sensitivity(), _stage(filter_node)])
            for name, filter_node in _filter_branches().items()
        })
        for name, tree in payloads.items():
            with self.subTest(branch=name):
                response, payload = self.fetch_json(
                    '/api/channel/response/validate/',
                    method='POST',
                    body={'response': tree},
                )
                self.assertEqual(response.code, 200)
                self.assertTrue(payload['valid'], msg=payload['issues'])

    def test_validation_returns_structured_xsd_errors(self):
        invalid = {
            'Response': {
                'children': [
                    {'Stage': {
                        'attributes': {'number': '-1'},
                        'children': [
                            {'StageGain': {'children': [
                                {'Value': 'bad'},
                                {'Frequency': '1'},
                            ]}},
                            {'StageGain': {'children': [
                                {'Value': '1'},
                                {'Frequency': '1'},
                            ]}},
                        ],
                    }},
                ],
            },
        }
        response, payload = self.fetch_json(
            '/api/channel/response/validate',
            method='POST',
            body={'response': invalid},
        )
        self.assertEqual(response.code, 200)
        self.assertTrue(payload['success'])
        self.assertFalse(payload['valid'])
        self.assertTrue(payload['issues'])
        self.assertTrue(any(issue['severity'] == 'error' for issue in payload['issues']))
        for issue in payload['issues']:
            self.assertEqual(set(issue), {'severity', 'code', 'path', 'message'})

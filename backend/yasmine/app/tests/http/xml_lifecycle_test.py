# 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
# HTTP coverage for xml CRUD, tree, wizard, library, import, nrl/arol mocks.

import os
from unittest.mock import MagicMock, patch

from yasmine.app.enums.xml_node import XmlNodeEnum
from yasmine.app.tests.common.http import YasmineHTTPTestCase
from yasmine.app.tests.integration.utils.integration_util import get_file_path


class XmlLifecycleHttpTest(YasmineHTTPTestCase):

    def _assert_json(self, response, payload, codes=(200,)):
        self.assertIn(response.code, codes, msg=getattr(response, 'body', b''))
        content_type = response.headers.get('Content-Type', '')
        self.assertIn('json', content_type.lower())
        self.assertTrue(isinstance(payload, (dict, list)), msg=payload)

    def _create_xml(self, name='lifecycle-xml'):
        response, payload = self.fetch_json('/api/xml/', method='POST', body={
            'id': -1,
            'name': name,
            'source': 'test',
            'module': 'yasmine-test',
            'uri': 'http://example.test',
            'sender': 'tester',
            'created_at': '2026-09-22T02:14:25',
        })
        self._assert_json(response, payload)
        self.assertTrue(payload.get('success'), msg=payload)
        self.assertEqual(payload.get('data', {}).get('created_at'), '2026-09-22T02:14:25')
        xml_id = payload.get('data', {}).get('id')
        self.assertIsNotNone(xml_id)
        return xml_id

    def test_xml_crud_tree_wizard_and_library(self):
        xml_id = self._create_xml()

        response, payload = self.fetch_json('/api/xml/%s' % xml_id)
        self._assert_json(response, payload)
        self.assertEqual(payload.get('data', {}).get('name'), 'lifecycle-xml')

        response, payload = self.fetch_json('/api/xml/%s' % xml_id, method='PUT', body={
            'id': xml_id,
            'name': 'lifecycle-xml-renamed',
            'source': 'test',
            'module': 'yasmine-test',
            'uri': 'http://example.test',
            'sender': 'tester',
            'created_at': '2026-09-22T02:14:25',
        })
        self._assert_json(response, payload)
        self.assertTrue(payload.get('success'))

        response, payload = self.fetch_json('/api/xml/tree/%s/' % xml_id, method='POST', body={
            'node_inst_id': 0,
            'parentId': None,
            'nodeType': XmlNodeEnum.NETWORK,
        })
        self._assert_json(response, payload)
        self.assertTrue(payload.get('success'))
        network_id = payload.get('data', {}).get('nodeId')
        self.assertIsNotNone(network_id)

        response, payload = self.fetch_json('/api/xml/tree/%s/' % xml_id)
        self._assert_json(response, payload)
        self.assertTrue(payload)

        response, payload = self.fetch_json('/api/xml/epoch/%s/' % xml_id)
        self.assertEqual(response.code, 200)

        response, payload = self.fetch_json('/api/xml/node-path/?nodeId=%s' % network_id)
        self._assert_json(response, payload)
        self.assertTrue(payload.get('success'))

        response, payload = self.fetch_json('/api/xml/node-path/?nodeId=999999')
        self._assert_json(response, payload, codes=(200, 400, 404, 500))

        response, payload = self.fetch_json('/api/xml/similar-channel/?xmlId=%s&nodeInstanceId=999999' % xml_id)
        self._assert_json(response, payload, codes=(200, 400, 404, 500))
        if response.code == 200:
            self.assertIn('success', payload)

        response, payload = self.fetch_json('/api/xml/attr/available/%s/' % network_id)
        self.assertIn(response.code, (200, 404, 500))

        response, payload = self.fetch_json('/api/xml/attr/validate/', method='POST', body={
            'node_id': XmlNodeEnum.NETWORK,
            'attr_name': 'code',
            'value': 'XX',
            'only_critical': True,
        })
        self.assertIn(response.code, (200, 400, 500))
        content_type = response.headers.get('Content-Type', '')
        if response.code >= 400:
            self.assertIn('json', content_type.lower())

        response, payload = self.fetch_json('/api/wizard/network/', method='POST', body={
            'xmlId': xml_id,
            'code': 'YY',
            'start_date': '2020-01-01T00:00:00',
            'end_date': None,
        })
        self._assert_json(response, payload)
        self.assertTrue(payload.get('success'))
        wizard_network_id = payload.get('network_id')
        self.assertIsNotNone(wizard_network_id)

        response, payload = self.fetch_json('/api/wizard/station/', method='POST', body={
            'xmlId': xml_id,
            'networkNodeId': wizard_network_id,
            'code': 'TST',
            'start_date': '2020-01-01T00:00:00',
            'latitude': 1.0,
            'longitude': 2.0,
            'elevation': 3.0,
        })
        self._assert_json(response, payload)
        self.assertTrue(payload.get('success'))
        station_id = payload.get('station_id')

        response, payload = self.fetch_json('/api/wizard/channel/%s/' % station_id)
        self._assert_json(response, payload)
        self.assertIn('data', payload)

        response, payload = self.fetch_json('/api/xml/validate/%s/' % xml_id)
        self.assertIn(response.code, (200, 400, 500))
        if response.code == 200:
            self.assertIsInstance(payload, dict)
            self.assertIn('errors', payload)
            self.assertIn('warnings', payload)
            self.assertIn('success', payload)
        else:
            self.assertIn('json', response.headers.get('Content-Type', '').lower())

        response, payload = self.fetch_json('/api/user-library/', method='POST', body={'name': 'lib-1'})
        self._assert_json(response, payload)
        self.assertTrue(payload.get('success'))
        library_id = payload.get('data', {}).get('id')
        self.assertIsNotNone(library_id)

        response, payload = self.fetch_json('/api/user-library/')
        self._assert_json(response, payload)
        self.assertTrue(payload.get('success'))

        response, payload = self.fetch_json('/api/user-library/node/', method='POST', body={
            'libraryId': library_id,
            'nodeType': XmlNodeEnum.NETWORK,
            'parentNodeId': None,
            'nodeIdToClone': None,
        })
        self._assert_json(response, payload, codes=(200, 400, 500))

        response, payload = self.fetch_json('/api/xml/%s' % xml_id, method='DELETE')
        self._assert_json(response, payload)
        self.assertTrue(payload.get('success'))

    def test_import_requires_xml_path(self):
        response, payload = self.fetch_json('/api/xml/ie/', method='POST', body={})
        self._assert_json(response, payload, codes=(200, 400))
        self.assertFalse(payload.get('success', True))

    def test_zip_import_requires_file(self):
        response, payload = self.fetch_json('/api/helper/zip-user-library/', method='POST', body={})
        self._assert_json(response, payload, codes=(200, 400))
        self.assertFalse(payload.get('success', True))

    def test_import_url_rejects_file_scheme(self):
        response, payload = self.fetch_json(
            '/api/helper/url-user-library/',
            method='POST',
            body={'url': 'file:///etc/passwd'},
        )
        self._assert_json(response, payload, codes=(200, 400, 500))
        self.assertFalse(payload.get('success', True))

    def test_import_stationxml_roundtrip_http(self):
        path = get_file_path('stationxmls/xx_v_1_2.xml')
        if not os.path.isfile(path):
            self.skipTest('fixture missing: %s' % path)
        with open(path, 'rb') as handle:
            xml_bytes = handle.read()
        boundary = '----YasmineTestBoundary'
        body = (
            b'--' + boundary.encode('ascii') + b'\r\n'
            b'Content-Disposition: form-data; name="name"\r\n\r\n'
            b'imported-xx\r\n'
            b'--' + boundary.encode('ascii') + b'\r\n'
            b'Content-Disposition: form-data; name="xml-path"; filename="xx_v_1_2.xml"\r\n'
            b'Content-Type: application/xml\r\n\r\n'
            + xml_bytes + b'\r\n'
            b'--' + boundary.encode('ascii') + b'--\r\n'
        )
        response = self.fetch(
            '/api/xml/ie/',
            method='POST',
            body=body,
            headers={'Content-Type': 'multipart/form-data; boundary=%s' % boundary},
        )
        self.assertEqual(response.code, 200, msg=response.body)
        payload = self.fetch_json('/api/xml/')[1]
        names = [row.get('name') for row in payload.get('data') or []]
        self.assertTrue(any(name and 'imported' in name for name in names) or any('xx' in (name or '') for name in names))

        xml_id = (payload.get('data') or [{}])[0].get('id')
        if xml_id:
            export = self.fetch('/api/xml/ie/%s' % xml_id)
            self.assertEqual(export.code, 200)
            self.assertIn(b'<', export.body[:200] if export.body else b'')

    def test_attr_and_help_and_helper(self):
        response, payload = self.fetch_json('/api/attr/1')
        self.assertEqual(response.code, 200)
        self.assertIsInstance(payload, list)

        response, payload = self.fetch_json('/api/help/xml_list/')
        self._assert_json(response, payload)
        self.assertIn('content', payload)

        response, payload = self.fetch_json('/api/help/missing_page/')
        self._assert_json(response, payload, codes=(404, 500))

        response, payload = self.fetch_json('/api/helper/1/1')
        self.assertEqual(response.code, 200)
        self.assertIsInstance(payload, list)

        response, payload = self.fetch_json('/api/cfg/0', method='PUT', body={
            'id': 0,
            'general__source': 'http-test-source',
        })
        self._assert_json(response, payload)
        self.assertTrue(payload.get('success'))

    def test_nrlv2_catalog_mocked(self):
        helper = MagicMock()
        helper.catalog.return_value = {'NRLCatalog': {'element': []}}
        with patch('yasmine.app.handlers.xml_nrlv2._get_nrlv2_helper', return_value=(helper, None)):
            response, payload = self.fetch_json('/api/nrlv2/catalog?level=element')
        self._assert_json(response, payload)
        self.assertTrue(payload.get('success'))

    def test_nrlv2_disabled_or_error_is_json(self):
        response, payload = self.fetch_json('/api/nrlv2/catalog')
        self._assert_json(response, payload, codes=(200, 400, 500))
        self.assertIn('success', payload)

    def test_nrl_and_arol_keys_mocked(self):
        nrl_helper = MagicMock()
        nrl_helper.get_sensors_keys.return_value = []
        nrl_helper.get_dataloggers_keys.return_value = []
        arol_helper = MagicMock()
        arol_helper.get_sensors_keys.return_value = []
        arol_helper.get_dataloggers_keys.return_value = []

        with patch('yasmine.app.handlers.xml_nrl.LibraryHelperFactory') as nrl_factory, \
                patch('yasmine.app.handlers.xml_ial.LibraryHelperFactory') as arol_factory:
            nrl_factory.return_value.get_helper.return_value = nrl_helper
            arol_factory.return_value.get_helper.return_value = arol_helper
            nrl_sensors = self.fetch_json('/api/nrl/sensors/')
            nrl_dataloggers = self.fetch_json('/api/nrl/dataloggers/')
            arol_sensors = self.fetch_json('/api/arol/sensor/key/')
            arol_dataloggers = self.fetch_json('/api/arol/datalogger/key/')

        self.assertEqual(nrl_sensors[0].code, 200)
        self.assertEqual(nrl_dataloggers[0].code, 200)
        self.assertEqual(arol_sensors[0].code, 200)
        self.assertEqual(arol_dataloggers[0].code, 200)

    def test_home_renders(self):
        response = self.fetch('/')
        self.assertEqual(response.code, 200)
        self.assertIn(b'html', response.body.lower()[:200] if response.body else b'html')
        self.assertIn(b'images/favicon.svg', response.body)

    def test_recalculate_sensitivity_does_not_nameerror(self):
        response_obj = MagicMock()
        response_obj.instrument_sensitivity.value = 123.0
        with patch(
            'yasmine.app.handlers.xml.load_response_from_preview_params',
            return_value=response_obj,
        ), patch(
            'yasmine.app.handlers.xml.recalculate_response_sensitivity',
            return_value=(response_obj, 1.0),
        ), patch(
            'yasmine.app.handlers.xml.response_obj_to_tree_json',
            return_value={'Response': {}},
        ), patch(
            'yasmine.app.handlers.xml.polynomial_or_polezero_response',
            return_value='text',
        ), patch(
            'yasmine.app.handlers.xml.ChannelUtils.create_response_plot',
            return_value='plot.png',
        ), patch(
            'yasmine.app.handlers.xml.ChannelUtils.create_response_csv',
            return_value='plot.csv',
        ):
            response, payload = self.fetch_json(
                '/api/channel/response/recalculate-sensitivity/',
                method='POST',
                body={'nodeInstanceId': 1},
            )
        self.assertEqual(response.code, 200, msg=getattr(response, 'body', b''))
        self.assertIsInstance(payload, dict, msg=payload)
        body = (response.body or b'').decode('utf-8', errors='replace')
        self.assertNotIn("name 'sys' is not defined", body)
        self.assertTrue(payload.get('success'), msg=payload)
        self.assertEqual(payload.get('sensitivity_value'), 123.0)

    def test_plot_url_missing_channel_is_json(self):
        response, payload = self.fetch_json(
            '/api/channel/response/plot-url/?nodeInstanceId=999999&min=0.01&max=10'
        )
        self._assert_json(response, payload)
        self.assertFalse(payload.get('success'))

    def test_difference_plot_url_missing_channels_is_json(self):
        response, payload = self.fetch_json(
            '/api/channel/response-difference/plot-url/'
            '?nodeInstance1Id=999998&nodeInstance2Id=999999&min=0.01&max=10'
        )
        self._assert_json(response, payload, codes=(200, 400, 404, 500))
        if isinstance(payload, dict):
            self.assertFalse(payload.get('success', True))

    def test_single_occurrence_attribute_cannot_be_duplicated(self):
        xml_id = self._create_xml('single-occurrence')
        response, payload = self.fetch_json('/api/xml/tree/%s/' % xml_id, method='POST', body={
            'node_inst_id': 0,
            'parentId': None,
            'nodeType': XmlNodeEnum.NETWORK,
        })
        self._assert_json(response, payload)
        network_id = payload['data']['nodeId']

        response, payload = self.fetch_json('/api/xml/attr/available/%s/' % network_id)
        self._assert_json(response, payload)
        historical = next(item for item in payload if item['name'] == 'historical_code')

        body = {
            'attr_id': historical['id'],
            'node_inst_id': network_id,
            'value_obj': 'DDD',
        }
        response, payload = self.fetch_json('/api/xml/attr/', method='POST', body=body)
        self._assert_json(response, payload)
        self.assertTrue(payload.get('success'), msg=payload)

        response, payload = self.fetch_json('/api/xml/attr/', method='POST', body={
            'attr_id': historical['id'],
            'node_inst_id': network_id,
            'value_obj': 'AAA',
        })
        self._assert_json(response, payload)
        self.assertFalse(payload.get('success'), msg=payload)

        response, payload = self.fetch_json('/api/xml/attr/available/%s/' % network_id)
        self._assert_json(response, payload)
        self.assertFalse(any(item['name'] == 'historical_code' for item in payload))

    def test_recalculate_sensitivity_missing_params_is_json(self):
        response, payload = self.fetch_json(
            '/api/channel/response/recalculate-sensitivity/',
            method='POST',
            body={},
        )
        self.assertEqual(response.code, 200, msg=getattr(response, 'body', b''))
        self.assertIsInstance(payload, dict, msg=payload)
        self.assertFalse(payload.get('success'))
        self.assertNotIn("name 'sys' is not defined", str(payload))

    def test_recalculate_sensitivity_options_returns_frequencies(self):
        options = {
            'normalization_frequency': 10.0,
            'sample_rate': 16.9833332,
            'auto_frequency': 4.2458333,
            'reported_sensitivity_value': 100.0,
            'reported_sensitivity_frequency': 1.0,
        }
        with patch(
            'yasmine.app.handlers.xml.load_response_from_preview_params',
            return_value=MagicMock(),
        ), patch(
            'yasmine.app.handlers.xml.get_sensitivity_recalculate_options',
            return_value=options,
        ):
            response, payload = self.fetch_json(
                '/api/channel/response/recalculate-sensitivity-options/',
                method='POST',
                body={'nodeInstanceId': 1},
            )
        self.assertEqual(response.code, 200, msg=getattr(response, 'body', b''))
        self.assertTrue(payload.get('success'), msg=payload)
        self.assertAlmostEqual(payload.get('auto_frequency'), 4.2458333)
        self.assertAlmostEqual(payload.get('normalization_frequency'), 10.0)
        self.assertAlmostEqual(payload.get('sample_rate'), 16.9833332)

    def test_recalculate_sensitivity_options_missing_params_is_json(self):
        response, payload = self.fetch_json(
            '/api/channel/response/recalculate-sensitivity-options/',
            method='POST',
            body={},
        )
        self.assertEqual(response.code, 200, msg=getattr(response, 'body', b''))
        self.assertIsInstance(payload, dict, msg=payload)
        self.assertFalse(payload.get('success'))

    def test_recalculate_sensitivity_auto_mode_calls_auto(self):
        response_obj = MagicMock()
        response_obj.instrument_sensitivity.value = 50.0
        with patch(
            'yasmine.app.handlers.xml.load_response_from_preview_params',
            return_value=response_obj,
        ), patch(
            'yasmine.app.handlers.xml.recalculate_response_sensitivity',
            return_value=(response_obj, 4.2458333),
        ) as mock_recalc, patch(
            'yasmine.app.handlers.xml.response_obj_to_tree_json',
            return_value={'Response': {}},
        ), patch(
            'yasmine.app.handlers.xml.polynomial_or_polezero_response',
            return_value='text',
        ), patch(
            'yasmine.app.handlers.xml.ChannelUtils.create_response_plot',
            return_value='plot.png',
        ), patch(
            'yasmine.app.handlers.xml.ChannelUtils.create_response_csv',
            return_value='plot.csv',
        ):
            response, payload = self.fetch_json(
                '/api/channel/response/recalculate-sensitivity/',
                method='POST',
                body={'nodeInstanceId': 1, 'frequencyMode': 'auto'},
            )
        self.assertEqual(response.code, 200, msg=getattr(response, 'body', b''))
        self.assertTrue(payload.get('success'), msg=payload)
        mock_recalc.assert_called_once_with(response_obj, auto=True)
        self.assertEqual(payload.get('sensitivity_frequency'), 4.2458333)

    def test_recalculate_sensitivity_custom_mode_passes_frequency(self):
        response_obj = MagicMock()
        response_obj.instrument_sensitivity.value = 50.0
        with patch(
            'yasmine.app.handlers.xml.load_response_from_preview_params',
            return_value=response_obj,
        ), patch(
            'yasmine.app.handlers.xml.recalculate_response_sensitivity',
            return_value=(response_obj, 1.0),
        ) as mock_recalc, patch(
            'yasmine.app.handlers.xml.response_obj_to_tree_json',
            return_value={'Response': {}},
        ), patch(
            'yasmine.app.handlers.xml.polynomial_or_polezero_response',
            return_value='text',
        ), patch(
            'yasmine.app.handlers.xml.ChannelUtils.create_response_plot',
            return_value='plot.png',
        ), patch(
            'yasmine.app.handlers.xml.ChannelUtils.create_response_csv',
            return_value='plot.csv',
        ):
            response, payload = self.fetch_json(
                '/api/channel/response/recalculate-sensitivity/',
                method='POST',
                body={
                    'nodeInstanceId': 1,
                    'frequencyMode': 'custom',
                    'frequency': 1.0,
                },
            )
        self.assertEqual(response.code, 200, msg=getattr(response, 'body', b''))
        self.assertTrue(payload.get('success'), msg=payload)
        mock_recalc.assert_called_once_with(response_obj, frequency=1.0)

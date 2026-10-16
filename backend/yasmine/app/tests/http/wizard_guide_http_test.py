# 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
# User-guide HTTP paths: wizard channels, map, extract, export, RESP import.

import json
from unittest.mock import patch
from urllib.parse import quote

from yasmine.app.enums.xml_node import XmlNodeAttrEnum, XmlNodeEnum
from yasmine.app.tests.common.http import YasmineHTTPTestCase
from yasmine.app.tests.unit.resp_import_test import PAZ_RESP


class WizardGuideHttpTest(YasmineHTTPTestCase):

    def _create_xml(self, name):
        response, payload = self.fetch_json('/api/xml/', method='POST', body={
            'id': -1,
            'name': name,
            'source': 'test',
            'module': 'yasmine-test',
            'uri': 'http://example.test',
            'sender': 'tester',
            'created_at': '2020-01-01T00:00:00',
        })
        self.assertEqual(response.code, 200, msg=getattr(response, 'body', b''))
        self.assertTrue(payload.get('success'), msg=payload)
        return payload['data']['id']

    def _create_network(self, xml_id, code='XX', end_date='2021-01-01T00:00:00'):
        response, payload = self.fetch_json('/api/wizard/network/', method='POST', body={
            'xmlId': xml_id,
            'code': code,
            'start_date': '2020-01-01T00:00:00',
            'end_date': end_date,
        })
        self.assertEqual(response.code, 200, msg=getattr(response, 'body', b''))
        self.assertTrue(payload.get('success'), msg=payload)
        return payload['network_id']

    def _create_station(self, xml_id, network_id, code='TST', latitude=50.0, longitude=80.0,
                        end_date='2021-01-01T00:00:00'):
        response, payload = self.fetch_json('/api/wizard/station/', method='POST', body={
            'xmlId': xml_id,
            'networkNodeId': network_id,
            'code': code,
            'start_date': '2020-01-01T00:00:00',
            'end_date': end_date,
            'latitude': latitude,
            'longitude': longitude,
            'elevation': 10.0,
        })
        self.assertEqual(response.code, 200, msg=getattr(response, 'body', b''))
        self.assertTrue(payload.get('success'), msg=payload)
        return payload['station_id']

    def _create_channels(self, xml_id, station_id, **extra):
        body = {
            'xmlId': xml_id,
            'stationNodeId': station_id,
            'libraryType': 'none',
            'start_date': '2020-01-01T00:00:00',
            'end_date': '2021-01-01T00:00:00',
            'latitude': 50.01,
            'longitude': 80.01,
            'elevation': 10.0,
            'depth': 0.0,
            'sampleRate': 100,
        }
        body.update(extra)
        response, payload = self.fetch_json('/api/wizard/new-channel/', method='POST', body=body)
        self.assertEqual(response.code, 200, msg=getattr(response, 'body', b''))
        return payload

    def _children(self, xml_id, parent_id):
        response, payload = self.fetch_json('/api/xml/tree/%s/%s' % (xml_id, parent_id))
        self.assertEqual(response.code, 200, msg=getattr(response, 'body', b''))
        self.assertIsInstance(payload, list)
        return payload

    def _attr_names(self, node_id):
        filt = json.dumps([{
            'property': 'node_inst_id',
            'value': node_id,
        }])
        response, payload = self.fetch_json('/api/xml/attr/?filter=%s' % quote(filt))
        self.assertEqual(response.code, 200, msg=getattr(response, 'body', b''))
        self.assertTrue(payload.get('success'), msg=payload)
        return [row.get('attr_name') for row in payload.get('data') or []]

    def test_wizard_channels_map_and_extract(self):
        xml_id = self._create_xml('guide-wizard')
        network_id = self._create_network(xml_id)
        station_id = self._create_station(xml_id, network_id)
        blank_id = self._create_station(
            xml_id, network_id, code='NIL', latitude=None, longitude=None, end_date=None,
        )
        self.assertIsNotNone(blank_id)

        response, station_prefill = self.fetch_json('/api/wizard/station/%s' % network_id)
        self.assertEqual(response.code, 200, msg=getattr(response, 'body', b''))
        self.assertEqual(
            (station_prefill.get('data') or {}).get('start_date'),
            '2020-01-01T00:00:00',
        )
        response, channel_prefill = self.fetch_json('/api/wizard/channel/%s' % station_id)
        self.assertEqual(response.code, 200, msg=getattr(response, 'body', b''))
        channel_data = channel_prefill.get('data') or {}
        self.assertEqual(channel_data.get('start_date'), '2020-01-01T00:00:00')
        self.assertEqual(float(channel_data.get('latitude')), 50.0)
        self.assertEqual(float(channel_data.get('longitude')), 80.0)
        self.assertEqual(float(channel_data.get('elevation')), 10.0)

        created = self._create_channels(
            xml_id,
            station_id,
            location_code='01',
            code1='BHZ',
            code2='BHN',
            code3='BHE',
            dip1=-90,
            dip2=0,
            dip3=0,
            azimuth1=0,
            azimuth2=0,
            azimuth3=90,
        )
        self.assertTrue(created.get('success'), msg=created)
        self.assertEqual(len(created.get('channel_ids') or []), 3)

        channels = self._children(xml_id, station_id)
        by_code = {row['code']: row for row in channels}
        self.assertEqual(set(by_code), {'BHZ', 'BHN', 'BHE'})
        for row in channels:
            self.assertAlmostEqual(float(row['sample_rate']), 100.0)
        self.assertIn(XmlNodeAttrEnum.DIP, self._attr_names(by_code['BHZ']['id']))
        self.assertIn(XmlNodeAttrEnum.AZIMUTH, self._attr_names(by_code['BHZ']['id']))

        soh = self._create_channels(
            xml_id,
            station_id,
            location_code='',
            code1='LDO',
            code2=None,
            code3=None,
            omitDipAzimuth=True,
            dip1=-90,
            azimuth1=0,
        )
        self.assertTrue(soh.get('success'), msg=soh)
        self.assertEqual(len(soh.get('channel_ids') or []), 1)
        soh_id = soh['channel_ids'][0]
        soh_names = self._attr_names(soh_id)
        self.assertNotIn(XmlNodeAttrEnum.DIP, soh_names)
        self.assertNotIn(XmlNodeAttrEnum.AZIMUTH, soh_names)

        missing = self._create_channels(xml_id, 999999, code1='BHZ')
        self.assertFalse(missing.get('success'))
        self.assertEqual(missing.get('channel_ids'), [])

        response, payload = self.fetch_json('/api/xml/map/%s/' % xml_id)
        self.assertEqual(response.code, 200)
        self.assertTrue(payload.get('success'), msg=payload)
        station_labels = [row['label'] for row in payload['data']['stations']]
        self.assertIn('XX.TST', station_labels)
        self.assertNotIn('XX.NIL', station_labels)
        self.assertEqual(payload['data']['channels'], [])

        response, payload = self.fetch_json('/api/xml/map/%s/?channels=1' % xml_id)
        self.assertEqual(response.code, 200)
        channel_labels = [row['label'] for row in payload['data']['channels']]
        self.assertIn('XX.TST.01.BHZ', channel_labels)
        self.assertIn('XX.TST.--.LDO', channel_labels)

        response, payload = self.fetch_json(
            '/api/xml/map/%s/?epoch=2022-01-01T00:00:00' % xml_id
        )
        self.assertEqual(response.code, 200)
        self.assertTrue(payload.get('success'), msg=payload)
        self.assertNotIn(
            'XX.TST',
            [row['label'] for row in payload['data']['stations']],
        )

        response, payload = self.fetch_json('/api/user-library/', method='POST', body={
            'name': 'guide-lib',
        })
        self.assertEqual(response.code, 200, msg=getattr(response, 'body', b''))
        self.assertTrue(payload.get('success'), msg=payload)
        library_id = payload['data']['id']

        response, payload = self.fetch_json('/api/user-library/node/', method='POST', body={
            'libraryId': library_id,
            'nodeType': XmlNodeEnum.NETWORK,
            'parentNodeId': None,
            'nodeIdToClone': network_id,
        })
        self.assertEqual(response.code, 200, msg=getattr(response, 'body', b''))
        self.assertTrue(payload.get('success'), msg=payload)

        response, payload = self.fetch_json(
            '/api/user-library/node/%s/%s/0' % (library_id, XmlNodeEnum.NETWORK)
        )
        self.assertEqual(response.code, 200, msg=getattr(response, 'body', b''))
        self.assertIn('XX', [row.get('code') for row in payload])

    def test_export_writes_12_and_warnings_do_not_block(self):
        xml_id = self._create_xml('guide-export')
        network_id = self._create_network(xml_id, code='XX')
        station_id = self._create_station(xml_id, network_id)
        created = self._create_channels(xml_id, station_id, code1='BHZ', location_code='01')
        self.assertTrue(created.get('success'), msg=created)

        exported = self.fetch('/api/xml/ie/%s' % xml_id)
        self.assertEqual(exported.code, 200, msg=exported.body)
        self.assertIn(b'schemaVersion="1.2"', exported.body)

        long_id = self._create_xml('guide-long-code')
        self._create_network(long_id, code='LONG_NETWORK_CODE')
        self._create_station(long_id, self._network_id_from_tree(long_id))
        warned = self.fetch('/api/xml/ie/%s' % long_id)
        self.assertEqual(warned.code, 200, msg=warned.body)
        self.assertIn(b'LONG_NETWORK_CODE', warned.body)
        self.assertIn(b'schemaVersion="1.2"', warned.body)

    def _network_id_from_tree(self, xml_id):
        response, payload = self.fetch_json('/api/xml/tree/%s/' % xml_id)
        self.assertEqual(response.code, 200, msg=getattr(response, 'body', b''))
        self.assertTrue(payload)
        return payload[0]['id']

    def test_export_blocked_when_validation_fails(self):
        xml_id = self._create_xml('guide-blocked')
        network_id = self._create_network(xml_id)
        self._create_station(xml_id, network_id)
        with patch(
            'yasmine.app.utils.imp_exp.validate_stationxml_12',
            return_value=[{'path': 'Network', 'message': 'forced', 'severity': 'error'}],
        ):
            response, payload = self.fetch_json('/api/xml/ie/%s' % xml_id)
        self.assertEqual(response.code, 400, msg=getattr(response, 'body', b''))
        self.assertTrue(str(payload.get('message', '')).startswith(
            'StationXML 1.2 export blocked'
        ))

    def test_import_resp_requires_a_file_and_stores_the_response(self):
        response, payload = self.fetch_json(
            '/api/channel/response/import-resp/',
            method='POST',
            body={},
        )
        self.assertEqual(response.code, 200, msg=getattr(response, 'body', b''))
        self.assertFalse(payload.get('success', True))

        xml_id = self._create_xml('guide-resp')
        network_id = self._create_network(xml_id)
        station_id = self._create_station(xml_id, network_id)
        created = self._create_channels(xml_id, station_id, code1='BHZ', location_code='00')
        self.assertTrue(created.get('success'), msg=created)
        channel_id = created['channel_ids'][0]

        boundary = '----YasmineRespBoundary'
        body = (
            b'--' + boundary.encode('ascii') + b'\r\n'
            b'Content-Disposition: form-data; name="nodeInstanceId"\r\n\r\n'
            + str(channel_id).encode('ascii') + b'\r\n'
            b'--' + boundary.encode('ascii') + b'\r\n'
            b'Content-Disposition: form-data; name="file"; filename="channel.resp"\r\n'
            b'Content-Type: application/octet-stream\r\n\r\n'
            + PAZ_RESP + b'\r\n'
            b'--' + boundary.encode('ascii') + b'--\r\n'
        )
        response = self.fetch(
            '/api/channel/response/import-resp/',
            method='POST',
            body=body,
            headers={'Content-Type': 'multipart/form-data; boundary=%s' % boundary},
        )
        self.assertEqual(response.code, 200, msg=response.body)
        payload = json.loads(response.body.decode('utf-8'))
        self.assertTrue(payload.get('success'), msg=payload)
        self.assertTrue(payload.get('data'))

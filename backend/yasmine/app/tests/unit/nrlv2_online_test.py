# 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
# ****************************************************************************
#
# Unit tests for NRLv2 Online helper
#
# NRLv2 online support (2026): ASGSR, Alexey Emanov.
#
# ****************************************************************************/

import io
import unittest
from unittest.mock import patch, MagicMock

from yasmine.app.handlers.equipment import EquipmentMixin
from yasmine.app.helpers.nrl.nrlv2_online import (
    Nrlv2OnlineHelper,
    Nrlv2OnlineError,
    _validate_url,
    _parse_instconfig_equipment,
    nrlv2_equipment_flags,
)


class Nrlv2OnlineHelperTest(unittest.TestCase):

    def test_validate_url_rejects_localhost(self):
        with self.assertRaises(Nrlv2OnlineError) as ctx:
            _validate_url('http://localhost/nrl/1/')
        self.assertEqual(ctx.exception.code, 'NRLV2_BAD_REQUEST')

    def test_validate_url_rejects_127(self):
        with self.assertRaises(Nrlv2OnlineError) as ctx:
            _validate_url('http://127.0.0.1/nrl/1/')
        self.assertEqual(ctx.exception.code, 'NRLV2_BAD_REQUEST')

    def test_validate_url_rejects_private(self):
        with self.assertRaises(Nrlv2OnlineError):
            _validate_url('http://192.168.1.1/nrl/1/')
        with self.assertRaises(Nrlv2OnlineError):
            _validate_url('http://10.0.0.1/nrl/1/')

    @patch('yasmine.app.utils.url_guard.socket.getaddrinfo', return_value=[(0, 0, 0, '', ('10.7.0.15', 8900))])
    def test_validate_url_accepts_internal_hostname(self, _mock_dns):
        _validate_url('http://vh07.gsn:8900/nrl/1')
        _validate_url('http://host.docker.internal:8000/nrl/1/')
        _mock_dns.assert_not_called()

    @patch('yasmine.app.utils.url_guard.socket.getaddrinfo', return_value=[(0, 0, 0, '', ('1.1.1.1', 443))])
    def test_validate_url_accepts_earthscope(self, _mock_dns):
        _validate_url('https://service.earthscope.org/irisws/nrl/1/')

    @patch('yasmine.app.utils.url_guard.socket.getaddrinfo', return_value=[(0, 0, 0, '', ('1.1.1.1', 443))])
    def test_validate_url_accepts_legacy_iris_host(self, _mock_dns):
        _validate_url('https://service.iris.edu/irisws/nrl/1/')

    def test_validate_url_rejects_file(self):
        with self.assertRaises(Nrlv2OnlineError):
            _validate_url('file:///etc/passwd')

    @patch('yasmine.app.helpers.nrl.nrlv2_online.requests.get')
    def test_catalog_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'NRLCatalog': {'element': [{'name': 'sensor'}, {'name': 'datalogger'}]}
        }
        helper = Nrlv2OnlineHelper(base_url='https://service.earthscope.org/irisws/nrl/1/')
        data = helper.catalog(level='element')
        self.assertIn('NRLCatalog', data)
        self.assertEqual(len(data['NRLCatalog']['element']), 2)

    @patch('yasmine.app.helpers.nrl.nrlv2_online.requests.get')
    def test_combine_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b'<?xml version="1.0"?><FDSNStationXML>...</FDSNStationXML>'
        helper = Nrlv2OnlineHelper(base_url='https://service.earthscope.org/irisws/nrl/1/')
        content = helper.combine('sensor_Guralp_CMG-3T_LP120_HF50_SG20000_STgroundVel')
        self.assertIn(b'FDSNStationXML', content)

    @patch('yasmine.app.helpers.nrl.nrlv2_online.requests.get')
    def test_catalog_404_raises(self, mock_get):
        mock_get.return_value.status_code = 404
        helper = Nrlv2OnlineHelper(base_url='https://service.earthscope.org/irisws/nrl/1/')
        with self.assertRaises(Nrlv2OnlineError) as ctx:
            helper.catalog(level='element')
        self.assertEqual(ctx.exception.code, 'NRLV2_EMPTY_RESULT')

    def test_equipment_flags_by_prefix(self):
        self.assertEqual(
            nrlv2_equipment_flags('sensor_Guralp_CMG-3T_LP120:datalogger_Quanterra_Q330_PG1'),
            (True, True),
        )
        self.assertEqual(
            nrlv2_equipment_flags('integrated_Gem_GemInfrasoundV1.0_SG1'),
            (True, True),
        )
        self.assertEqual(
            nrlv2_equipment_flags('soh_Quanterra_Q330HR_VM1'),
            (False, True),
        )
        self.assertEqual(nrlv2_equipment_flags(''), (False, False))

    @patch('yasmine.app.utils.url_guard.socket.getaddrinfo', return_value=[(0, 0, 0, '', ('1.1.1.1', 443))])
    def test_element_keys_and_configurations(self, _mock_dns):
        helper = Nrlv2OnlineHelper(base_url='https://service.earthscope.org/irisws/nrl/1/')
        helper.catalog = MagicMock(side_effect=[
            {
                'NRLCatalog': {
                    'element': [{
                        'manufacturer': [
                            {'name': 'Gem', 'detail': 'Gem help text'},
                            {'name': 'GeoSIG'},
                        ]
                    }]
                }
            },
            {
                'NRLCatalog': {
                    'element': [{
                        'manufacturer': [{
                            'model': [{
                                'configuration': [{
                                    'instconfig': 'soh_Quanterra_Q330_VM1',
                                    'description': 'mass position',
                                    'parameters': {'Input': 'Mass position'},
                                }, {
                                    'instconfig': 'soh_Quanterra_Q330_VT1',
                                    'description': 'voltage',
                                    'parameters': {'Input': 'Voltage'},
                                }]
                            }]
                        }]
                    }]
                }
            },
        ])
        keys = helper.get_element_keys('integrated')
        self.assertEqual([item['key'] for item in keys], ['Gem', 'GeoSIG'])
        self.assertEqual(keys[0]['help'], 'Gem help text')
        self.assertEqual(keys[1]['help'], '')
        helper.catalog.assert_called_with(element='integrated', level='manufacturer')
        configs = helper.get_element_configurations('soh', 'Quanterra', 'Q330')
        self.assertEqual(configs['configurations'][0]['instconfig'], 'soh_Quanterra_Q330_VM1')
        self.assertEqual(configs['parameterNames'], ['Input'])
        self.assertEqual(configs['parameterOptions']['Input'], ['*', 'Mass position', 'Voltage'])

    @patch('yasmine.app.utils.url_guard.socket.getaddrinfo', return_value=[(0, 0, 0, '', ('1.1.1.1', 443))])
    def test_element_keys_rejects_unknown_element(self, _mock_dns):
        helper = Nrlv2OnlineHelper(base_url='https://service.earthscope.org/irisws/nrl/1/')
        with self.assertRaises(Nrlv2OnlineError) as ctx:
            helper.get_element_keys('amplifier')
        self.assertEqual(ctx.exception.code, 'NRLV2_BAD_REQUEST')

    def test_parse_instconfig_equipment(self):
        eq = _parse_instconfig_equipment('sensor_Guralp_CMG-3T_LP120_HF50_SG20000_STgroundVel')
        self.assertEqual(eq.manufacturer, 'Guralp')
        self.assertEqual(eq.model, 'CMG-3T')
        self.assertIn('sensor_Guralp', eq.description)


class _EquipmentRecorder(EquipmentMixin):
    def __init__(self):
        self.db = MagicMock()
        self.created = []

    def recreate_attr(self, node_inst, attr_name):
        self.created.append(attr_name)
        return MagicMock()


class Nrlv2EquipmentRolesTest(unittest.TestCase):

    def _helper(self):
        helper = MagicMock()
        response = MagicMock()
        response.response_stages = None
        helper.get_channel_response_obj.return_value = response
        helper.get_element_response_obj.return_value = response
        helper.get_sensor_equipment.return_value = MagicMock()
        helper.get_datalogger_equipment.return_value = MagicMock()
        helper.get_element_equipment.side_effect = lambda element, keys: MagicMock()
        return helper

    def test_integrated_instconfig_fills_sensor_and_datalogger(self):
        recorder = _EquipmentRecorder()
        helper = self._helper()
        with patch('yasmine.app.handlers.equipment.LibraryHelperFactory') as factory:
            factory.return_value.get_helper.return_value = helper
            sensor, datalogger, _rate, response = recorder.manage_equipment_nrlv2(
                MagicMock(), 'integrated_Gem_GemInfrasoundV1.0_SG1'
            )
        self.assertIsNotNone(sensor)
        self.assertIsNotNone(datalogger)
        self.assertIsNotNone(response)
        self.assertEqual(recorder.created, ['sensor', 'data_logger', 'response'])

    def test_soh_instconfig_fills_datalogger_only(self):
        recorder = _EquipmentRecorder()
        helper = self._helper()
        with patch('yasmine.app.handlers.equipment.LibraryHelperFactory') as factory:
            factory.return_value.get_helper.return_value = helper
            sensor, datalogger, _rate, response = recorder.manage_equipment_nrlv2(
                MagicMock(), 'soh_Quanterra_Q330_VM1'
            )
        self.assertIsNone(sensor)
        self.assertIsNotNone(datalogger)
        self.assertIsNotNone(response)
        self.assertEqual(recorder.created, ['data_logger', 'response'])

    def test_offline_integrated_and_soh_roles(self):
        recorder = _EquipmentRecorder()
        helper = self._helper()
        sensor, datalogger, _rate, _response = recorder.manage_equipment_nrl_element(
            MagicMock(), helper, 'integrated', ['Gem', 'Gem.resp']
        )
        self.assertIsNotNone(sensor)
        self.assertIsNotNone(datalogger)
        self.assertEqual(helper.get_element_equipment.call_count, 2)

        recorder.created = []
        sensor, datalogger, _rate, _response = recorder.manage_equipment_nrl_element(
            MagicMock(), helper, 'soh', ['Generic', 'Unity.resp']
        )
        self.assertIsNone(sensor)
        self.assertIsNotNone(datalogger)
        self.assertEqual(recorder.created, ['data_logger', 'response'])

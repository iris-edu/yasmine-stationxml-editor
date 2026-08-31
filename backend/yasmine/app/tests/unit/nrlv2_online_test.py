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

from yasmine.app.helpers.nrl.nrlv2_online import (
    Nrlv2OnlineHelper,
    Nrlv2OnlineError,
    _validate_url,
    _parse_instconfig_equipment,
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

    def test_validate_url_accepts_earthscope(self):
        _validate_url('https://service.earthscope.org/irisws/nrl/1/')

    def test_validate_url_accepts_legacy_iris_host(self):
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

    def test_parse_instconfig_equipment(self):
        eq = _parse_instconfig_equipment('sensor_Guralp_CMG-3T_LP120_HF50_SG20000_STgroundVel')
        self.assertEqual(eq.manufacturer, 'Guralp')
        self.assertEqual(eq.model, 'CMG-3T')
        self.assertIn('sensor_Guralp', eq.description)

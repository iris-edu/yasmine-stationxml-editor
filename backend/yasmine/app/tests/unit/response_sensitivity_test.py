# ****************************************************************************
#
# Unit tests for response sensitivity recalculation.
#
# ****************************************************************************/

import unittest
from unittest.mock import MagicMock, patch

from obspy.core.inventory.response import (
    CoefficientsTypeResponseStage,
    InstrumentSensitivity,
    Response,
)


from yasmine.app.utils.response_sensitivity import (
    PolynomialResponseError,
    get_updated_response_obj,
    load_response_from_preview_params,
    merge_response_into_station_xml,
    preview_plot_basename,
    recalculate_response_sensitivity,
    response_obj_to_tree_json_standalone,
    response_tree_to_obj,
)


def _gain_stage(sequence_number, gain, input_units='M/S', output_units='V'):
    return CoefficientsTypeResponseStage(
        stage_sequence_number=sequence_number,
        stage_gain=gain,
        stage_gain_frequency=1.0,
        input_units=input_units,
        output_units=output_units,
        cf_transfer_function_type='DIGITAL',
        numerator=[1.0],
        denominator=[1.0],
        decimation_factor=1,
        decimation_input_sample_rate=100.0,
        decimation_offset=0,
        decimation_delay=0,
        decimation_correction=0,
    )


class RecalculateResponseSensitivityTest(unittest.TestCase):

    def test_recalculate_updates_value_from_stages(self):
        response = _mock_response([2000.0, 4.0], sensitivity_value=100.0)
        updated, freq = recalculate_response_sensitivity(response)
        self.assertEqual(freq, 1.0)
        self.assertAlmostEqual(updated.instrument_sensitivity.value, 8000.0, places=3)

    def test_changed_stage_gain_changes_sensitivity(self):
        response = _mock_response([2000.0, 4.0])
        _, _ = recalculate_response_sensitivity(response)
        first_value = response.instrument_sensitivity.value

        response.response_stages[1].stage_gain = 8.0
        _, _ = recalculate_response_sensitivity(response)
        self.assertNotAlmostEqual(response.instrument_sensitivity.value, first_value, places=3)
        self.assertAlmostEqual(response.instrument_sensitivity.value, 16000.0, places=3)

    def test_polynomial_raises(self):
        response = MagicMock()
        response.instrument_polynomial = MagicMock()
        with self.assertRaises(PolynomialResponseError):
            recalculate_response_sensitivity(response)

    def test_uses_instrument_sensitivity_frequency(self):
        response = _mock_response([10.0, 2.0], output_units='V')
        response.instrument_sensitivity.frequency = 2.0
        _, freq = recalculate_response_sensitivity(response)
        self.assertEqual(freq, 2.0)


def _mock_response(stage_gains, sensitivity_value=1.0, output_units='V'):
    stages = []
    for i, gain in enumerate(stage_gains):
        in_u = 'M/S' if i == 0 else 'V'
        out_u = 'V' if i < len(stage_gains) - 1 else output_units
        stages.append(_gain_stage(i + 1, gain, input_units=in_u, output_units=out_u))
    sens = InstrumentSensitivity(
        value=sensitivity_value,
        frequency=1.0,
        input_units='M/S',
        output_units=output_units,
    )
    return Response(response_stages=stages, instrument_sensitivity=sens)


class LoadResponseFromPreviewParamsTest(unittest.TestCase):

    @patch('yasmine.app.utils.response_sensitivity.LibraryHelperFactory')
    def test_load_from_instconfig(self, mock_factory):
        mock_helper = MagicMock()
        mock_response = _mock_response([10.0, 2.0])
        mock_helper.get_channel_response_obj.return_value = mock_response
        mock_factory.return_value.get_helper.return_value = mock_helper

        result = load_response_from_preview_params({
            'instconfig': 'sensor_x:datalogger_y',
            'source': 'asgsr',
        }, handler=MagicMock(application=MagicMock()))

        self.assertIs(result, mock_response)
        mock_helper.get_channel_response_obj.assert_called_once_with(
            'sensor_x:datalogger_y', source='asgsr',
        )

    @patch('yasmine.app.utils.response_sensitivity.LibraryHelperFactory')
    def test_load_from_library_keys(self, mock_factory):
        mock_helper = MagicMock()
        mock_response = _mock_response([5.0, 3.0])
        mock_helper.get_channel_response_obj.return_value = mock_response
        mock_factory.return_value.get_helper.return_value = mock_helper

        result = load_response_from_preview_params({
            'libraryType': 'nrl',
            'sensorKeys': ['sensor', 'a'],
            'dataloggerKeys': ['datalogger', 'b'],
        })

        self.assertIs(result, mock_response)
        mock_helper.get_channel_response_obj.assert_called_once_with(
            ['sensor', 'a'], ['datalogger', 'b'],
        )

    def test_load_requires_identifiers(self):
        with self.assertRaises(ValueError):
            load_response_from_preview_params({})


class ResponseTreeRoundTripTest(unittest.TestCase):

    def test_response_tree_to_obj_round_trip(self):
        response = _mock_response([2000.0, 4.0], sensitivity_value=100.0)
        tree = response_obj_to_tree_json_standalone(response)
        restored = response_tree_to_obj(tree)
        self.assertAlmostEqual(
            restored.instrument_sensitivity.value,
            response.instrument_sensitivity.value,
            places=3,
        )

    def test_get_updated_response_obj_inserts_missing_response(self):
        from obspy.core.inventory import Channel, Station, Network, Inventory, Site
        from obspy import UTCDateTime
        import io

        response = _mock_response([2000.0, 4.0], sensitivity_value=100.0)
        tree = response_obj_to_tree_json_standalone(response)
        from yasmine.app.utils.response_sensitivity import prepare_response_json_as_xml
        xml_frag = prepare_response_json_as_xml(tree)

        start = UTCDateTime(2020, 1, 1)
        ch = Channel(
            code='HHZ', location_code='00', latitude=0, longitude=0, elevation=0,
            depth=0, azimuth=0, dip=0, sample_rate=100, start_date=start,
        )
        st = Station(
            code='YY', latitude=0, longitude=0, elevation=0, start_date=start,
            site=Site('Mock'), channels=[ch],
        )
        net = Network(code='XX', stations=[st], start_date=start)
        inv = Inventory(networks=[net], source='Y', module='Y', module_uri='', created=start)
        out = io.BytesIO()
        inv.write(out, format='STATIONXML')
        station_xml = out.getvalue().decode('utf-8')

        restored = get_updated_response_obj(xml_frag, station_xml)
        self.assertAlmostEqual(restored.instrument_sensitivity.value, 100.0, places=3)

    def test_merge_response_into_station_xml_inserts_before_channel_end(self):
        station_xml = '<Channel><SampleRate>100</SampleRate></Channel>'
        merged = merge_response_into_station_xml('<Response><Value>1</Value></Response>', station_xml)
        self.assertIn('<Response>', merged)
        self.assertTrue(merged.index('<Response>') < merged.index('</Channel>'))

    def test_preview_plot_basename_instconfig(self):
        name = preview_plot_basename({
            'instconfig': 'sensor_a:datalogger_b',
        })
        self.assertTrue(name.startswith('wizard_preview_'))


class ResponseAttributeRoutingTest(unittest.TestCase):

    def test_string_value_is_not_library_or_tree_payload(self):
        from unittest.mock import MagicMock
        from yasmine.app.enums.xml_node import XmlNodeAttrEnum
        from yasmine.app.services.attribute_service import AttributeService

        obj = MagicMock()
        obj.attr.name = XmlNodeAttrEnum.RESPONSE
        text = 'Channel Response\n\tOverall Sensitivity: 2000'
        self.assertFalse(AttributeService._is_edit_response_attribute(obj, text))
        self.assertFalse(AttributeService._is_new_response_attribute(obj, text))

    def test_library_payload_routes_to_new_response(self):
        from unittest.mock import MagicMock
        from yasmine.app.enums.xml_node import XmlNodeAttrEnum
        from yasmine.app.services.attribute_service import AttributeService

        obj = MagicMock()
        obj.attr.name = XmlNodeAttrEnum.RESPONSE
        payload = {
            'libraryType': 'nrlv2_online',
            'instconfig': 'sensor_a:datalogger_b',
            'recalculateSensitivity': True,
        }
        self.assertTrue(AttributeService._is_new_response_attribute(obj, payload))
        self.assertFalse(AttributeService._is_edit_response_attribute(obj, payload))


    def test_recalculate_equipment_response_uses_last_tuple_item(self):
        from unittest.mock import MagicMock
        from yasmine.app.services.attribute_service import AttributeService

        response = _mock_response([2000.0, 4.0], sensitivity_value=100.0)
        response_attr = MagicMock()
        response_attr.attr = None
        response_attr.value_obj = response
        AttributeService._recalculate_equipment_response((MagicMock(), MagicMock(), MagicMock(), response_attr))
        self.assertAlmostEqual(response_attr.value_obj.instrument_sensitivity.value, 8000.0, places=3)


class RecalculateSensitivityIntegrationTest(unittest.TestCase):
    """Smoke test against NRLaggregator when available."""

    @classmethod
    def setUpClass(cls):
        try:
            import requests
            r = requests.get(
                'http://host.docker.internal:8000/nrl/1/catalog',
                params={'level': 'element', 'format': 'json'},
                timeout=3,
            )
            cls.nrl_available = r.status_code == 200
        except Exception:
            cls.nrl_available = False

    def test_vel_cascade_recalculate(self):
        if not self.nrl_available:
            self.skipTest('NRLaggregator not available')
        from yasmine.app.helpers.nrl.nrlv2_online import Nrlv2OnlineHelper

        instconfig = (
            'sensor_Kazgeofizpribor_SK-1P_LP2_TD0.7_SG200_STgroundVel:'
            'datalogger_Expas_Baikal-8L_FV2.5Vp_FR400_CT2UserFIR'
        )
        helper = Nrlv2OnlineHelper(base_url='http://host.docker.internal:8000/nrl/1/')
        response = helper.get_channel_response_obj(instconfig, source='asgsr')
        old_value = response.instrument_sensitivity.value
        updated, _ = recalculate_response_sensitivity(response)
        self.assertIsNotNone(updated.instrument_sensitivity.value)
        self.assertAlmostEqual(updated.instrument_sensitivity.value, old_value, places=0)


if __name__ == '__main__':
    unittest.main()

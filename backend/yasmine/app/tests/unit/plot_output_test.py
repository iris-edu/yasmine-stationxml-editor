# ****************************************************************************
#
# Unit tests for response plot output unit detection (DISP/VEL/ACC).
#
# ****************************************************************************/

import unittest
from unittest.mock import MagicMock

from obspy.core.inventory.response import InstrumentSensitivity, Response

from yasmine.app.helpers.base_helper import _normalize_response_units
from yasmine.app.utils.response_plot import (
    detect_plot_output,
    amplitude_ylabel,
    diff_amplitude_ylabel,
    apply_bode_axis_labels,
)


def _mock_response(stage0_input, sens_input=None):
    stage0 = MagicMock()
    stage0.input_units = stage0_input
    stage0.input_units_description = stage0_input
    sens = InstrumentSensitivity(
        value=1.0,
        frequency=1.0,
        input_units=sens_input or stage0_input,
        output_units='COUNTS',
    )
    return Response(response_stages=[stage0], instrument_sensitivity=sens)


class DetectPlotOutputTest(unittest.TestCase):

    def test_instconfig_ground_vel(self):
        self.assertEqual(
            detect_plot_output(None, 'sensor_Guralp_CMG-3T_LP120_STgroundVel'),
            'VEL',
        )

    def test_instconfig_ground_accel(self):
        self.assertEqual(
            detect_plot_output(None, 'sensor_EQMet_TSA_STgroundAccel'),
            'ACC',
        )

    def test_instconfig_ground_disp(self):
        self.assertEqual(
            detect_plot_output(None, 'sensor_Test_STgroundDisp'),
            'DISP',
        )

    def test_instconfig_takes_priority_over_response(self):
        resp = _mock_response('M/S**2')
        self.assertEqual(
            detect_plot_output(resp, 'sensor_X_STgroundVel'),
            'VEL',
        )

    def test_stage0_accel_units(self):
        resp = _mock_response('M/S**2')
        self.assertEqual(detect_plot_output(resp), 'ACC')

    def test_stage0_vel_units(self):
        resp = _mock_response('M/S')
        self.assertEqual(detect_plot_output(resp), 'VEL')

    def test_stage0_disp_units(self):
        resp = _mock_response('M')
        self.assertEqual(detect_plot_output(resp), 'DISP')

    def test_unknown_units_fallback_def(self):
        resp = _mock_response('V')
        self.assertEqual(detect_plot_output(resp), 'DEF')

    def test_empty_response_fallback_def(self):
        self.assertEqual(detect_plot_output(None), 'DEF')


class AmplitudeYlabelTest(unittest.TestCase):

    def test_amplitude_ylabel_vel(self):
        self.assertEqual(amplitude_ylabel('VEL'), 'Amplitude [m/s]')

    def test_amplitude_ylabel_accel(self):
        self.assertEqual(amplitude_ylabel('ACC'), 'Amplitude [m/s²]')

    def test_amplitude_ylabel_disp(self):
        self.assertEqual(amplitude_ylabel('DISP'), 'Amplitude [m]')

    def test_amplitude_ylabel_def_from_sensitivity(self):
        resp = _mock_response('M/S', sens_input='M/S')
        resp.instrument_sensitivity.output_units = 'COUNTS'
        self.assertEqual(amplitude_ylabel('DEF', resp), 'Amplitude [counts/m/s]')

    def test_amplitude_ylabel_def_without_sensitivity(self):
        self.assertEqual(amplitude_ylabel('DEF', None), 'Amplitude')

    def test_diff_amplitude_ylabel_includes_type(self):
        self.assertIn('velocity', diff_amplitude_ylabel('VEL'))
        self.assertIn('acceleration', diff_amplitude_ylabel('ACC'))

    def test_apply_bode_axis_labels_sets_frequency_hz(self):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        fig = plt.figure()
        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212)
        apply_bode_axis_labels(fig, 'VEL', plot_degrees=False)
        self.assertEqual(ax1.get_ylabel(), 'Amplitude [m/s]')
        self.assertEqual(ax2.get_xlabel(), 'Frequency [Hz]')
        self.assertEqual(ax2.get_ylabel(), 'Phase [rad]')
        plt.close(fig)


class NormalizeResponseUnitsTest(unittest.TestCase):

    def test_preserves_accel_on_sensitivity(self):
        stage0 = MagicMock()
        stage0.input_units = 'M/S**2'
        stage0.input_units_description = 'Acceleration'
        stage0.output_units = 'V'
        dl_stage = MagicMock()
        dl_stage.input_units = None
        dl_stage.output_units = 'COUNTS'
        sens = InstrumentSensitivity(
            value=1.0,
            frequency=1.0,
            input_units='M/S',
            output_units='COUNTS',
        )
        resp = Response(
            response_stages=[stage0, dl_stage],
            instrument_sensitivity=sens,
        )
        _normalize_response_units(resp)
        self.assertIn('**2', str(resp.instrument_sensitivity.input_units).upper())


class PlotOutputIntegrationTest(unittest.TestCase):
    """Smoke tests against NRLaggregator when available."""

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

    def _load_cascade(self, instconfig):
        import io
        import requests
        from obspy import read_inventory
        from yasmine.app.helpers.nrl.nrlv2_online import Nrlv2OnlineHelper

        helper = Nrlv2OnlineHelper(base_url='http://host.docker.internal:8000/nrl/1/')
        return helper.get_channel_response_obj(instconfig, source='asgsr')

    def test_vel_cascade_plot_output(self):
        if not self.nrl_available:
            self.skipTest('NRLaggregator not available')
        ic = (
            'sensor_Kazgeofizpribor_SK-1P_LP2_TD0.7_SG200_STgroundVel:'
            'datalogger_Expas_Baikal-8L_FV2.5Vp_FR400_CT2UserFIR'
        )
        resp = self._load_cascade(ic)
        self.assertEqual(detect_plot_output(resp, ic), 'VEL')
        iu = str(resp.instrument_sensitivity.input_units).upper()
        self.assertIn('M/S', iu)
        self.assertNotIn('**2', iu)

    def test_accel_cascade_plot_output(self):
        if not self.nrl_available:
            self.skipTest('NRLaggregator not available')
        ic = (
            'sensor_R-Sensors_MTSS-1043A_LP100_HF120_SG1.2_STgroundAccel:'
            'datalogger_Expas_Baikal-8L_FV2.5Vp_FR400_CT2UserFIR'
        )
        resp = self._load_cascade(ic)
        self.assertEqual(detect_plot_output(resp, ic), 'ACC')
        iu = str(resp.instrument_sensitivity.input_units).upper()
        self.assertIn('**2', iu)

    def test_vel_and_accel_amplitudes_differ(self):
        if not self.nrl_available:
            self.skipTest('NRLaggregator not available')
        import numpy as np
        dl = 'datalogger_Expas_Baikal-8L_FV2.5Vp_FR400_CT2UserFIR'
        ic_vel = f'sensor_Kazgeofizpribor_SK-1P_LP2_TD0.7_SG200_STgroundVel:{dl}'
        ic_acc = f'sensor_R-Sensors_MTSS-1043A_LP100_HF120_SG1.2_STgroundAccel:{dl}'
        resp_vel = self._load_cascade(ic_vel)
        resp_acc = self._load_cascade(ic_acc)
        freqs = np.logspace(-2, 1, 20)
        amp_vel = np.abs(resp_vel.get_evalresp_response_for_frequencies(freqs, output='VEL'))
        amp_acc = np.abs(resp_acc.get_evalresp_response_for_frequencies(freqs, output='ACC'))
        self.assertFalse(np.allclose(amp_vel, amp_acc, rtol=0.01))

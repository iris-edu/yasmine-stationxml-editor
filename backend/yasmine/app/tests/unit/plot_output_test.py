# 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
# ****************************************************************************
#
# Unit tests for response plot output unit detection (DISP/VEL/ACC).
#
# ****************************************************************************/

import unittest
from unittest.mock import MagicMock

from obspy.core.inventory.response import InstrumentSensitivity, Response

from yasmine.app.helpers.base_helper import _normalize_response_units
from yasmine.app.helpers.utils.utils import plot_max_frequency, response_nyquist
from yasmine.app.utils.response_plot import (
    detect_plot_output,
    amplitude_ylabel,
    diff_amplitude_ylabel,
    apply_bode_axis_labels,
    _wrap_phase,
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

    def test_response_units_win_over_instconfig(self):
        resp = _mock_response('M/S**2')
        self.assertEqual(
            detect_plot_output(resp, 'sensor_X_STgroundVel'),
            'ACC',
        )

    def test_instconfig_used_when_response_units_are_unknown(self):
        resp = _mock_response('V')
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
        self.assertEqual(amplitude_ylabel('VEL'), 'Amplitude [counts/m/s]')

    def test_amplitude_ylabel_accel(self):
        self.assertEqual(amplitude_ylabel('ACC'), 'Amplitude [counts/m/s²]')

    def test_amplitude_ylabel_disp(self):
        self.assertEqual(amplitude_ylabel('DISP'), 'Amplitude [counts/m]')

    def test_amplitude_ylabel_uses_response_output_unit(self):
        resp = _mock_response('M/S**2')
        resp.instrument_sensitivity.output_units = 'V'
        self.assertEqual(amplitude_ylabel('ACC', resp), 'Amplitude [v/m/s²]')

    def test_amplitude_ylabel_def_from_sensitivity(self):
        resp = _mock_response('M/S', sens_input='M/S')
        resp.instrument_sensitivity.output_units = 'COUNTS'
        self.assertEqual(amplitude_ylabel('DEF', resp), 'Amplitude [counts/m/s]')

    def test_amplitude_ylabel_prefers_explicit_sensitivity(self):
        resp = _mock_response('M/S', sens_input='M/S')
        resp.instrument_sensitivity.output_units = 'COUNTS'
        stage_sens = InstrumentSensitivity(
            value=10.0,
            frequency=0.05,
            input_units='M/S',
            output_units='V',
        )
        self.assertEqual(
            amplitude_ylabel('DEF', resp, sensitivity=stage_sens),
            'Amplitude [v/m/s]',
        )

    def test_amplitude_ylabel_ground_motion_uses_explicit_output(self):
        resp = _mock_response('M/S**2')
        resp.instrument_sensitivity.output_units = 'COUNTS'
        stage_sens = InstrumentSensitivity(
            value=1.0,
            frequency=1.0,
            input_units='M/S**2',
            output_units='V',
        )
        self.assertEqual(
            amplitude_ylabel('ACC', resp, sensitivity=stage_sens),
            'Amplitude [v/m/s²]',
        )

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
        self.assertEqual(ax1.get_ylabel(), 'Amplitude [counts/m/s]')
        self.assertEqual(ax2.get_xlabel(), 'Frequency [Hz]')
        self.assertEqual(ax2.get_ylabel(), 'Phase [rad]')
        plt.close(fig)


class WrapPhaseTest(unittest.TestCase):

    def test_wraps_a_branch_cut_jump_into_the_bode_range(self):
        import numpy as np
        wrapped = _wrap_phase(np.array([190.0, -190.0, 10.0, np.nan]), True)
        self.assertAlmostEqual(wrapped[0], -170.0)
        self.assertAlmostEqual(wrapped[1], 170.0)
        self.assertAlmostEqual(wrapped[2], 10.0)
        self.assertTrue(np.isnan(wrapped[3]))


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


class PlotMaxFrequencyTest(unittest.TestCase):

    def test_empty_max_uses_nyquist(self):
        stage = MagicMock()
        stage.decimation_input_sample_rate = 200
        stage.decimation_factor = 1
        response = MagicMock(response_stages=[stage])
        self.assertEqual(plot_max_frequency(response, None), 100)

    def test_unknown_rate_uses_100_hz(self):
        response = MagicMock(response_stages=[])
        self.assertEqual(plot_max_frequency(response, None), 100)

    def test_non_numeric_stage_rate_falls_back(self):
        response = MagicMock()
        self.assertIsNone(response_nyquist(response))
        self.assertEqual(plot_max_frequency(response, None), 100)

    def test_requested_max_is_the_drawn_limit(self):
        response = MagicMock(response_stages=[])
        self.assertEqual(plot_max_frequency(response, 25), 25)

    def test_requested_max_above_sample_rate_is_clamped(self):
        stage = MagicMock()
        stage.decimation_input_sample_rate = 200
        stage.decimation_factor = 1
        response = MagicMock(response_stages=[stage])
        self.assertEqual(plot_max_frequency(response, 500), 200)
        self.assertEqual(response_nyquist(response), 100)

    def test_sample_rate_above_20000_caps_at_20000(self):
        stage = MagicMock()
        stage.decimation_input_sample_rate = 40000
        stage.decimation_factor = 1
        response = MagicMock(response_stages=[stage])
        self.assertEqual(plot_max_frequency(response, 30000), 20000)

    def test_low_min_reduces_max_to_point_budget(self):
        stage = MagicMock()
        stage.decimation_input_sample_rate = 4000
        stage.decimation_factor = 1
        response = MagicMock(response_stages=[stage])
        self.assertEqual(plot_max_frequency(response, 4000, 0.0001), 200)

    def test_empty_max_also_obeys_point_budget(self):
        stage = MagicMock()
        stage.decimation_input_sample_rate = 200
        stage.decimation_factor = 1
        response = MagicMock(response_stages=[stage])
        self.assertEqual(plot_max_frequency(response, None, 0.00001), 20)

    def test_unknown_rate_requested_max_caps_at_20000(self):
        response = MagicMock(response_stages=[])
        self.assertEqual(plot_max_frequency(response, 25000), 20000)
        self.assertIsNone(response_nyquist(response))

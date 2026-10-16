# 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
# ****************************************************************************
#
# Plot failures must report the evalresp reason, not ObsPy's generic code.
#
# ****************************************************************************/

import unittest
from unittest.mock import MagicMock

from obspy.core.inventory.response import InstrumentSensitivity, Response

from yasmine.app.utils.response_plot import format_plot_failure, format_sensitivity_failure


class FormatPlotFailureTest(unittest.TestCase):

    def test_zero_stage0_sensitivity_replaces_illegal_resp_format(self):
        response = Response(
            instrument_sensitivity=InstrumentSensitivity(0.0, 21.2308, 'PA', 'COUNT'),
            response_stages=[],
        )
        message = format_plot_failure(
            ValueError('norm_resp: Illegal RESP format'),
            response,
        )
        self.assertIn('Stage 0 sensitivity is 0', message)
        self.assertIn('21.2308', message)
        self.assertIn('zero stage gain', message)
        self.assertIn('non-zero number', message)
        self.assertNotIn('Illegal RESP format', message)
        self.assertNotIn('units mismatch', message)

    def test_zero_stage_gain(self):
        stage = MagicMock()
        stage.stage_sequence_number = 2
        stage.stage_gain = 0.0
        stage.input_units = 'V'
        stage.output_units = 'COUNT'
        response = MagicMock()
        response.instrument_sensitivity = None
        response.response_stages = [stage]
        message = format_plot_failure(
            ValueError('norm_resp: Illegal RESP format'),
            response,
        )
        self.assertIn('Stage 2 gain is 0', message)
        self.assertIn('product of every stage gain', message)
        self.assertNotIn('Illegal RESP format', message)

    def test_units_mismatch(self):
        first = MagicMock()
        first.stage_sequence_number = 1
        first.stage_gain = 1.0
        first.input_units = 'M/S'
        first.output_units = 'V'
        second = MagicMock()
        second.stage_sequence_number = 2
        second.stage_gain = 1.0
        second.input_units = 'PA'
        second.output_units = 'COUNT'
        response = MagicMock()
        response.instrument_sensitivity = MagicMock(value=1.0)
        response.response_stages = [first, second]
        message = format_plot_failure(
            ValueError('check_channel: Illegal RESP format'),
            response,
        )
        self.assertIn('Units mismatch at stage 2', message)
        self.assertIn('v followed by pa', message)
        self.assertIn('previous stage\'s output units', message)

    def test_other_errors_stay_unchanged(self):
        message = format_plot_failure(ValueError('matplotlib failed'), None)
        self.assertEqual(message, 'Cannot generate plot.<br>matplotlib failed')

    def test_missing_stage_gain_explains_norm_resp(self):
        stage = MagicMock()
        stage.stage_sequence_number = 1
        stage.stage_gain = None
        stage.stage_gain_frequency = None
        response = MagicMock()
        response.instrument_sensitivity = None
        response.response_stages = [stage]
        message = format_sensitivity_failure(
            ValueError('norm_resp: Illegal RESP format'),
            response,
        )
        self.assertIn('Cannot recalculate sensitivity.', message)
        self.assertIn('Stage 1 has no StageGain', message)
        self.assertIn('no stage gain defined', message)
        self.assertNotIn('Illegal RESP format', message)

    def test_missing_decimation_explains_check_channel(self):
        stage = CoefficientsTypeResponseStage()
        response = MagicMock()
        response.instrument_sensitivity = MagicMock(value=1.0)
        response.response_stages = [stage]
        message = format_plot_failure(
            ValueError('check_channel: Illegal RESP format'),
            response,
        )
        self.assertIn('Stage 2 has no Decimation', message)
        self.assertIn('input sample rate', message)
        self.assertNotIn('Illegal RESP format', message)

    def test_unknown_illegal_resp_lists_norm_resp_causes(self):
        message = format_sensitivity_failure(
            ValueError('norm_resp: Illegal RESP format'),
            None,
        )
        self.assertIn('Cannot recalculate sensitivity.', message)
        self.assertIn('InstrumentSensitivity (stage 0) is 0', message)
        self.assertIn('StageGain value is 0', message)
        self.assertIn('no StageGain', message)
        self.assertNotIn('check_channel', message)


class CoefficientsTypeResponseStage(object):
    """Stand-in whose class name matches ObsPy's coefficients stage."""

    def __init__(self):
        self.stage_sequence_number = 2
        self.stage_gain = 1.0
        self.stage_gain_frequency = 1.0
        self.input_units = 'COUNT'
        self.output_units = 'COUNT'
        self.decimation_input_sample_rate = None
        self.decimation_factor = None
        self.pz_transfer_function_type = None

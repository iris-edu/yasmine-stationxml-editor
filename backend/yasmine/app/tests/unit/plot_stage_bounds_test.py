# 2026-09-29, version 4.4.0-beta: ASGSR, Alexey Emanov
# ****************************************************************************
#
# Unit tests for response plot stage listing and start/end bounds.
#
# ****************************************************************************/

import unittest
from unittest.mock import MagicMock

from yasmine.app.helpers.utils.utils import (
    parse_plot_stage_bounds,
    plot_marker_sensitivity,
    response_plot_stages,
)
from yasmine.app.utils.response_plot import amplitude_ylabel


class ResponsePlotStagesTest(unittest.TestCase):

    def test_lists_sequence_numbers_and_labels(self):
        stage1 = type('PolesZerosResponseStage', (), {
            'stage_sequence_number': 1,
        })()
        stage2 = type('CoefficientsTypeResponseStage', (), {
            'stage_sequence_number': 2,
        })()
        response = MagicMock(response_stages=[stage1, stage2])
        stages = response_plot_stages(response)
        self.assertEqual(stages, [
            {'number': 1, 'label': 'Stage 1: PolesZeros'},
            {'number': 2, 'label': 'Stage 2: Coefficients'},
        ])

    def test_empty_stages(self):
        response = MagicMock(response_stages=[])
        self.assertEqual(response_plot_stages(response), [])


class ParsePlotStageBoundsTest(unittest.TestCase):

    def test_defaults_to_full_chain(self):
        self.assertEqual(parse_plot_stage_bounds(None, None), (1, None))

    def test_single_stage_range(self):
        self.assertEqual(parse_plot_stage_bounds(3, 3), (3, 3))

    def test_rejects_start_after_end(self):
        with self.assertRaises(ValueError):
            parse_plot_stage_bounds(4, 2)

    def test_clamps_unknown_end_stage_to_last(self):
        stages = [
            type('PolesZerosResponseStage', (), {'stage_sequence_number': n})()
            for n in (1, 2, 3)
        ]
        response = MagicMock(response_stages=stages)
        self.assertEqual(parse_plot_stage_bounds(1, 5, response), (1, 3))

    def test_clamps_unknown_start_stage_to_first(self):
        stage1 = type('PolesZerosResponseStage', (), {'stage_sequence_number': 1})()
        response = MagicMock(response_stages=[stage1])
        self.assertEqual(parse_plot_stage_bounds(2, None, response), (1, None))

    def test_accepts_string_numbers(self):
        self.assertEqual(parse_plot_stage_bounds('1', '2'), (1, 2))


class PlotMarkerSensitivityTest(unittest.TestCase):

    def _stage(self, number, gain, frequency, input_units='M/S', output_units='V'):
        stage = MagicMock()
        stage.stage_sequence_number = number
        stage.stage_gain = gain
        stage.stage_gain_frequency = frequency
        stage.input_units = input_units
        stage.output_units = output_units
        return stage

    def test_full_chain_keeps_instrument_sensitivity(self):
        overall = MagicMock(value=123.0, frequency=1.0)
        response = MagicMock(
            response_stages=[
                self._stage(1, 10.0, 1.0),
                self._stage(2, 2.0, 1.0, 'V', 'counts'),
            ],
            instrument_sensitivity=overall,
        )
        self.assertIs(plot_marker_sensitivity(response, 1, 2), overall)

    def test_single_stage_uses_stage_gain(self):
        overall = MagicMock(value=999.0, frequency=5.0)
        response = MagicMock(
            response_stages=[
                self._stage(1, 10.0, 0.05),
                self._stage(2, 2.0, 1.0, 'V', 'counts'),
            ],
            instrument_sensitivity=overall,
        )
        marker = plot_marker_sensitivity(response, 1, 1)
        self.assertEqual(float(marker.value), 10.0)
        self.assertEqual(float(marker.frequency), 0.05)
        self.assertNotEqual(float(marker.value), float(overall.value))

    def test_stage_range_multiplies_gains(self):
        response = MagicMock(
            response_stages=[
                self._stage(1, 10.0, 0.05),
                self._stage(2, 2.0, 1.0, 'V', 'counts'),
                self._stage(3, 0.5, 1.0, 'counts', 'counts'),
            ],
            instrument_sensitivity=MagicMock(value=999.0, frequency=1.0),
        )
        marker = plot_marker_sensitivity(response, 2, 3)
        self.assertEqual(float(marker.value), 1.0)
        self.assertEqual(float(marker.frequency), 1.0)

    def test_stage1_ylabel_uses_stage_units_not_full_chain(self):
        overall = MagicMock(value=999.0, frequency=5.0, input_units='M/S', output_units='COUNTS')
        response = MagicMock(
            response_stages=[
                self._stage(1, 10.0, 0.05, 'M/S', 'V'),
                self._stage(2, 2.0, 1.0, 'V', 'COUNTS'),
            ],
            instrument_sensitivity=overall,
        )
        marker = plot_marker_sensitivity(response, 1, 1)
        self.assertEqual(
            amplitude_ylabel('DEF', response, sensitivity=marker),
            'Amplitude [v/m/s]',
        )
        self.assertEqual(
            amplitude_ylabel('DEF', response),
            'Amplitude [counts/m/s]',
        )

    def test_stage_range_ylabel_uses_selected_units(self):
        response = MagicMock(
            response_stages=[
                self._stage(1, 10.0, 0.05, 'M/S', 'V'),
                self._stage(2, 2.0, 1.0, 'V', 'COUNTS'),
                self._stage(3, 0.5, 1.0, 'COUNTS', 'COUNTS'),
            ],
            instrument_sensitivity=MagicMock(
                value=999.0, frequency=1.0, input_units='M/S', output_units='COUNTS',
            ),
        )
        marker = plot_marker_sensitivity(response, 2, 3)
        self.assertEqual(
            amplitude_ylabel('DEF', response, sensitivity=marker),
            'Amplitude [counts/v]',
        )


if __name__ == '__main__':
    unittest.main()

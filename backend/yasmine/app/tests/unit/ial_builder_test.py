# 2026-09-18, version 4.1.3-beta: ASGSR, Alexey Emanov
# AROL response builder must not IndexError / UnboundLocalError on odd datalogger lists.

import unittest
from unittest.mock import MagicMock, patch

from yasmine.app.helpers.ial.ial_channel_response_builder import IalChannelResponseBuilder


def _sensor():
    return [{
        'response': {
            'stages': [{
                'name': 'sensor',
                'gain': {'value': 1.0, 'frequency': 1.0},
                'input_units': {'name': 'M/S', 'description': 'VELOCITY'},
                'output_units': {'name': 'V', 'description': 'VOLTS'},
                'filter': {'type': 'PolesZeros', 'zeros': [], 'poles': []},
                'extras': [],
            }]
        }
    }]


def _datalogger(n_stages=1, name='DIGITIZER'):
    stages = []
    for i in range(n_stages):
        stages.append({
            'name': name,
            'gain': {'value': 1.0, 'frequency': 1.0},
            'input_units': {'name': 'V', 'description': 'VOLTS'},
            'output_units': {'name': 'COUNTS', 'description': 'COUNTS'},
            'filter': {'type': 'DIGITAL'},
            'input_sample_rate': 100,
            'output_sample_rate': 100,
            'extras': [{}],
        })
    return {'response': {'stages': stages}}


class IalChannelResponseBuilderTest(unittest.TestCase):

    def test_single_datalogger_does_not_index_error(self):
        builder = IalChannelResponseBuilder()
        stage = MagicMock()
        stage.stage_gain = 1.0
        stage.input_units = 'M/S'
        stage.output_units = 'V'
        with patch.object(builder, 'stage_dict_to_ResponseStage', return_value=stage), \
                patch.object(builder, 'get_preamp_stage', return_value=stage):
            try:
                builder.build(_sensor(), [_datalogger()])
            except (IndexError, UnboundLocalError) as err:
                self.fail('single datalogger raised %s' % err.__class__.__name__)
            except Exception:
                pass

    def test_three_dataloggers_returns_none(self):
        builder = IalChannelResponseBuilder()
        with patch.object(builder, 'stage_dict_to_ResponseStage', return_value=MagicMock()):
            result = builder.build(_sensor(), [_datalogger(), _datalogger(), _datalogger()])
            self.assertIsNone(result)


class NormalizationTest(unittest.TestCase):

    def test_digital_normalization_is_not_the_laplace_value(self):
        laplace = IalChannelResponseBuilder.getNormalization(1.0, [0j], [], 'A')
        digital = IalChannelResponseBuilder.getNormalization(1.0, [0j], [], 'D', 100.0)
        self.assertNotAlmostEqual(laplace, digital)

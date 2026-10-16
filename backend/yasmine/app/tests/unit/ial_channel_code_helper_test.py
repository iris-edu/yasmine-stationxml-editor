# 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
# 2026-09-29, version 4.4.0-beta: ASGSR, Alexey Emanov
# AROL channel-code helper uses seed_channel_prefix when responses are available.

import unittest

from yasmine.app.helpers.ial.ial_channel_code_helper import IalChannelCodeHelper


class IalChannelCodeHelperTest(unittest.TestCase):

    def test_guess_code_empty_without_responses(self):
        self.assertEqual(IalChannelCodeHelper().guess_code(None, None), ('', ''))
        self.assertEqual(IalChannelCodeHelper().guess_code(['a'], ['b']), ('', ''))

    def test_guess_code_from_sample_rate_and_units(self):
        sensor = {
            'description': 'broadband seismometer',
            'response': {
                'stages': [{
                    'input_units': {'name': 'M/S', 'description': 'Velocity'},
                    'normalization_frequency': 1.0,
                }]
            },
        }
        datalogger = {
            'response': {
                'stages': [{
                    'decimation_input_sample_rate': 100.0,
                    'decimation_factor': 1,
                }]
            },
        }
        stem, band = IalChannelCodeHelper().guess_code(sensor, datalogger)
        self.assertIn(band, 'FGDCESHBMLVURWPQ')
        self.assertTrue(stem)
        self.assertTrue(stem[0].isalpha())

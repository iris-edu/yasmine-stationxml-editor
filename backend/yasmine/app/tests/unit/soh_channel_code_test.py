# 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
# ****************************************************************************
#
# Unit tests for SOH SEED channel-code suggestions.
#
# ****************************************************************************/

import unittest

from yasmine.app.helpers.nrl.soh_channel_code import (
    description_from_keys,
    description_from_units,
    parse_sample_rate,
    parse_soh_resp,
    suggest_soh_code,
)


_RESP = """\
B054F05     Response in units lookup:              celsius - Temperature in degrees Celsius
B057F04     Input sample rate (HZ):                 1.0000E-01
"""


class SohChannelCodeTest(unittest.TestCase):

    def test_band_follows_sample_rate(self):
        self.assertEqual(suggest_soh_code('Temperature', '0.1 Hz')['code'], 'VKI')
        self.assertEqual(suggest_soh_code('Temperature', '1 Hz')['code'], 'LKI')
        self.assertEqual(suggest_soh_code('ClockQuality', 1)['code'], 'LCQ')

    def test_known_descriptions(self):
        cases = {
            'MassPosition': ('VM', 'VM'),
            'Voltage': ('VE', 'VEP'),
            'InputVoltage': ('VE', 'VEP'),
            'Current': ('VE', 'VEC'),
            'SystemCurrent': ('VE', 'VEC'),
            'AntennaCurrent': ('VE', 'VEA'),
            'InternalTemperature': ('VK', 'VKI'),
            'ClockError': ('LC', 'LCE'),
            'CrystalOscillator': ('VC', 'VCO'),
            'BufferUsage': ('VP', 'VPB'),
        }
        for description, (prefix, code) in cases.items():
            rate = '1 Hz' if description in ('ClockError',) else '0.1 Hz'
            if description == 'ClockQuality':
                rate = '1 Hz'
            suggestion = suggest_soh_code(description, rate)
            self.assertEqual(suggestion['prefix'], prefix, description)
            self.assertEqual(suggestion['code'], code, description)

    def test_unknown_description_keeps_band_only(self):
        suggestion = suggest_soh_code('SomethingElse', '0.1 Hz')
        self.assertEqual(suggestion['band'], 'V')
        self.assertEqual(suggestion['instrument'], '')
        self.assertEqual(suggestion['prefix'], 'V')
        self.assertEqual(suggestion['code'], 'V')

    def test_description_from_instconfig_key(self):
        keys = ['soh_Quanterra_Q330_CDMassPosition_SG10_FR0.1']
        self.assertEqual(description_from_keys(keys), 'MassPosition')
        self.assertIsNone(description_from_keys(['Unity.resp']))

    def test_resp_units_and_rate(self):
        units, rate = parse_soh_resp(_RESP)
        self.assertEqual(units, 'celsius')
        self.assertAlmostEqual(rate, 0.1)
        self.assertEqual(description_from_units(units), 'Temperature')
        self.assertIsNone(description_from_units('percent'))

    def test_parse_sample_rate_edges(self):
        self.assertIsNone(parse_sample_rate(None))
        self.assertIsNone(parse_sample_rate(''))
        self.assertIsNone(parse_sample_rate('no number'))
        self.assertAlmostEqual(parse_sample_rate('1.0E-01 Hz'), 0.1)
        self.assertEqual(parse_sample_rate(1), 1.0)

    def test_parse_soh_resp_empty_and_units_only(self):
        self.assertEqual(parse_soh_resp(''), (None, None))
        self.assertEqual(parse_soh_resp(None), (None, None))
        units, rate = parse_soh_resp('B054F05     Response in units lookup:              V\n')
        self.assertEqual(units, 'V')
        self.assertIsNone(rate)

    def test_description_from_keys_empty(self):
        self.assertIsNone(description_from_keys(None))
        self.assertIsNone(description_from_keys([]))

    def test_suggest_without_rate_keeps_instrument(self):
        suggestion = suggest_soh_code('Temperature', None)
        self.assertEqual(suggestion['instrument'], 'K')
        self.assertEqual(suggestion['band'], '')
        self.assertEqual(suggestion['prefix'], 'K')
        self.assertEqual(suggestion['code'], 'KI')

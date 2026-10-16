# 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
# NRL SEED band and combined channel-code rules.

import os
import tempfile
import unittest

from yasmine.app.helpers.nrl.nrl_channel_code_helper import NrlChannelCodeHelper


class NrlChannelCodeHelperTest(unittest.TestCase):

    def setUp(self):
        self.helper = NrlChannelCodeHelper(None, None)

    def test_band_code_table(self):
        cases = (
            (1000, False, 'F'),
            (1000, True, 'G'),
            (250, False, 'C'),
            (80, False, 'H'),
            (80, True, 'E'),
            (10, False, 'B'),
            (10, True, 'S'),
            (5, False, 'M'),
            (1, False, 'L'),
            (0.1, False, 'V'),
            (0.01, False, 'U'),
            (0.0005, False, 'R'),
            (5e-5, False, 'P'),
            (1e-6, False, 'T'),
            (5e-7, False, 'Q'),
        )
        for rate, short, expected in cases:
            self.assertEqual(self.helper.band_code(rate, short), expected, rate)

    def test_band_code_unknown_and_missing(self):
        self.assertIsNone(self.helper.band_code(None))
        self.assertIsNone(self.helper.band_code(0.05))

    def test_combine_broadband_and_short_period(self):
        self.assertEqual(self.helper.combine_channel_codes('BHZ', 'HHZ'), 'HHZ')
        self.assertEqual(self.helper.combine_channel_codes('SHZ', 'HHZ'), 'EHZ')
        self.assertEqual(self.helper.combine_channel_codes('SHZ', 'CHZ'), 'DHZ')
        self.assertEqual(self.helper.combine_channel_codes('SHZ', 'FHZ'), 'GHZ')
        self.assertEqual(self.helper.combine_channel_codes('SHZ', 'BHZ'), 'SHZ')
        self.assertEqual(self.helper.combine_channel_codes(None, 'HHZ'), 'ZZZ')

    def test_single_channel_sensors(self):
        self.assertTrue(self.helper.is_single_channel('BDF'))
        self.assertTrue(self.helper.is_single_channel('BHE'))
        self.assertFalse(self.helper.is_single_channel('BHZ'))

    def test_read_channel_code_from_resp(self):
        folder = tempfile.mkdtemp()
        path = os.path.join(folder, 'sensor.resp')
        try:
            with open(path, 'w') as handle:
                handle.write('B052F03     Location:\nB052F04     Channel:                               BHZ\n')
            tree = {'Guralp': {'CMG': ('desc', path)}}
            self.assertEqual(
                self.helper.read_channel_code_from_NRL(['Guralp', 'CMG'], tree),
                'BHZ',
            )
        finally:
            os.remove(path)
            os.rmdir(folder)

    def test_guess_code_uses_datalogger_rate(self):
        folder = tempfile.mkdtemp()
        sensor = os.path.join(folder, 'sensor.resp')
        datalogger = os.path.join(folder, 'datalogger.resp')
        try:
            with open(sensor, 'w') as handle:
                handle.write('B052F04     Channel:                               BHZ\n')
            with open(datalogger, 'w') as handle:
                handle.write('B052F04     Channel:                               HHZ\n')
            helper = NrlChannelCodeHelper(
                {'Guralp': {'CMG': ('s', sensor)}},
                {'Quanterra': {'Q330': ('d', datalogger)}},
            )
            chan, band = helper.guess_code(
                ['Guralp', 'CMG'],
                ['Quanterra', 'Q330'],
                '100 Hz causal',
            )
            self.assertEqual(chan, 'HHZ')
            self.assertEqual(band, 'H')
        finally:
            os.remove(sensor)
            os.remove(datalogger)
            os.rmdir(folder)

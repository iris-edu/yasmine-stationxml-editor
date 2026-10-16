# 2026-09-25, version 4.3.3-beta: ASGSR, Alexey Emanov
# ****************************************************************************
#
# Unit tests for SEED channel-prefix suggestions.
#
# ****************************************************************************/

import unittest

from yasmine.app.helpers.nrl.seed_channel_prefix import (
    angular_period_from_keys,
    angular_period_from_low_frequency_corner,
    band_code,
    input_units_from_text,
    parse_angular_period,
    sample_rate_from_keys,
    response_sample_rate_and_units,
    suggest_channel_prefix,
    units_and_legacy_from_resp,
)


class SeedChannelPrefixTest(unittest.TestCase):

    def test_angular_period_is_reciprocal_of_natural_frequency(self):
        self.assertEqual(parse_angular_period('120 s'), 120)
        self.assertAlmostEqual(parse_angular_period('4.5 Hz'), 1 / 4.5)

    def test_band_uses_angular_period_above_10_hz(self):
        self.assertEqual(band_code(100, '120 s'), 'H')
        self.assertEqual(band_code(20, 120), 'B')
        self.assertEqual(band_code(100, '1 s'), 'E')
        self.assertEqual(band_code(100, None), 'H')
        self.assertEqual(band_code(0.1, 120), 'V')
        self.assertEqual(band_code(1, 1), 'L')
        self.assertEqual(band_code(1.05, 120), 'L')
        self.assertEqual(band_code(5e-5, None), 'P')
        self.assertEqual(band_code(5e-6, None), 'T')

    def test_helper_and_soh_use_same_band_authority(self):
        from yasmine.app.helpers.nrl.nrl_channel_code_helper import NrlChannelCodeHelper
        from yasmine.app.helpers.nrl.soh_channel_code import suggest_soh_code

        helper = NrlChannelCodeHelper(None, None)
        # ≈1 Hz must stay L (legacy helper used to return M for rate > 1 first).
        self.assertEqual(helper.band_code(1.05, short_period=False), 'L')
        self.assertEqual(band_code(1.05, None), 'L')
        self.assertEqual(suggest_soh_code('ClockQuality', 1.05)['band'], 'L')
        self.assertEqual(helper.band_code(100, short_period=True), 'E')
        self.assertEqual(band_code(100, 1.0), 'E')
        self.assertEqual(helper.band_code(100, short_period=False), 'H')

    def test_velocity_broadband_prefix(self):
        suggestion = suggest_channel_prefix('groundVel', '120 s', '100 Hz')
        self.assertEqual(suggestion['prefix'], 'HH')

    def test_low_frequency_corner_sets_short_period_band(self):
        text = (
            'RSensors; MTSS-1001; Low-Frequency_Corner 1 Hz; '
            'High-Frequency_Corner 300 Hz; Sensor_Type groundVel'
        )
        self.assertAlmostEqual(angular_period_from_low_frequency_corner(text), 1)
        short = suggest_channel_prefix('groundVel', '1 Hz', 100)
        self.assertEqual(short['prefix'], 'EH')
        broad = suggest_channel_prefix('groundVel', '0.0083 Hz', 100)
        self.assertEqual(broad['prefix'], 'HH')
        self.assertIsNone(angular_period_from_low_frequency_corner(
            'Long-Period_Corner 120 s; High-Frequency_Corner 50 Hz'
        ))

    def test_short_period_and_geophone(self):
        short = suggest_channel_prefix('groundVel', '1 s', 100)
        self.assertEqual(short['prefix'], 'EH')
        geophone = suggest_channel_prefix('groundVel', '5 Hz', 100)
        self.assertEqual(geophone['instrument'], 'P')
        self.assertEqual(geophone['band'], 'E')
        standard = suggest_channel_prefix('groundVel', '4.5 Hz', 100)
        self.assertEqual(standard['instrument'], 'P')
        self.assertEqual(standard['prefix'], 'EP')
        displacement = suggest_channel_prefix(None, '4.5 Hz', 100, input_units='M')
        self.assertEqual(displacement['instrument'], 'H')

    def test_units_infer_velocity_or_acceleration(self):
        velocity = suggest_channel_prefix(None, None, 100, input_units='M/S')
        self.assertEqual(velocity['prefix'], 'HH')
        self.assertEqual(velocity['instrument'], 'H')
        acceleration = suggest_channel_prefix(
            'unknown', None, 100, input_units='M/S**2'
        )
        self.assertEqual(acceleration['prefix'], 'HN')
        short = suggest_channel_prefix(None, '1 s', 100, input_units='cm/s^2')
        self.assertEqual(short['prefix'], 'EN')

    def test_acceleration_pressure_and_low_gain(self):
        self.assertEqual(
            suggest_channel_prefix('groundAcc', None, 100)['prefix'], 'HN'
        )
        pascals = suggest_channel_prefix(None, 30, 20, input_units='Pa')
        self.assertEqual(pascals['prefix'], 'BD')
        self.assertFalse(pascals['orientationApplies'])
        self.assertEqual(pascals['code'], 'BDO')
        infrasound = suggest_channel_prefix(
            None, 30, 20, input_units='Pa', description='infrasound'
        )
        self.assertFalse(infrasound['orientationApplies'])
        self.assertEqual(infrasound['code'], 'BDF')
        low = suggest_channel_prefix(
            'groundVel', '120 s', 20, description='Low gain seismometer'
        )
        self.assertEqual(low['prefix'], 'BL')
        air = suggest_channel_prefix('airPressure', '30 s', 20)
        self.assertFalse(air['orientationApplies'])
        self.assertEqual(air['code'], 'BDF')
        weather = suggest_channel_prefix('airPressure', '30 s', 20, description='barometer')
        self.assertEqual(weather['code'], 'BDO')
        self.assertTrue(suggest_channel_prefix('groundVel', '120 s', 20)['orientationApplies'])

    def test_seed_appendix_a_families(self):
        """Instrument letter, third letter and dip/azimuth follow Appendix A."""
        cases = (
            # Seismometer: M, M/S, M/S**2. Gravimeter G, mass position M, geophone P.
            (dict(input_units='M', sample_rate=100), 'HH', True, 'HH'),
            (dict(input_units='M/S', sample_rate=100), 'HH', True, 'HH'),
            (dict(input_units='M/S**2', sample_rate=100), 'HN', True, 'HN'),
            (dict(sensor_type='gravimeter', input_units='M/S**2', sample_rate=100), 'HG', True, 'HG'),
            (dict(sensor_type='massPosition', sample_rate=100), 'HM', True, 'HM'),
            (dict(sensor_type='geophone', sample_rate=100), 'HP', True, 'HP'),
            # Tilt is radians and keeps a direction. Rotation is rad/s and rad/s^2.
            (dict(input_units='rad', sample_rate=20, angular_period=30), 'BA', True, 'BA'),
            (dict(input_units='rad/s', sample_rate=20, angular_period=30), 'BJ', True, 'BJ'),
            (dict(input_units='rad/s**2', sample_rate=20, angular_period=30), 'BJ', True, 'BJ'),
            # Creep uses meters and a fault azimuth. Calibration has no direction.
            (dict(sensor_type='creep', input_units='M', sample_rate=20, angular_period=30), 'BB', True, 'BB'),
            (dict(sensor_type='calibration', sample_rate=20, angular_period=30), 'BC', False, 'BC'),
            # Pressure, humidity, temperature: place letter, no dip/azimuth.
            (dict(input_units='%', sample_rate=20, angular_period=30), 'BI', False, 'BIO'),
            (dict(input_units='%', sample_rate=20, angular_period=30, description='inside'), 'BI', False, 'BII'),
            (dict(input_units='degC', sample_rate=20, angular_period=30), 'BK', False, 'BKO'),
            (dict(input_units='degK', sample_rate=20, angular_period=30, description='downhole'), 'BK', False, 'BKD'),
            # Electronic test point: V → P, A → C. Electric potential stays Q.
            (dict(input_units='V', sample_rate=20, angular_period=30), 'BE', False, 'BEP'),
            (dict(input_units='A', sample_rate=20, angular_period=30), 'BE', False, 'BEC'),
            (dict(input_units='Hz', sample_rate=20, angular_period=30), 'BE', False, 'BE'),
            (dict(sensor_type='electric', input_units='V', sample_rate=20, angular_period=30), 'BQ', True, 'BQ'),
            # Magnetometer is ZNE unless it records total intensity.
            (dict(input_units='T', sample_rate=20, angular_period=30), 'BF', True, 'BF'),
            (dict(input_units='nT', sample_rate=20, angular_period=30, description='total intensity'), 'BF', False, 'BF'),
            # Water current and linear strain keep a direction. Tide is vertical.
            (dict(sensor_type='waterCurrent', input_units='M/S', sample_rate=20, angular_period=30), 'BO', True, 'BO'),
            (dict(input_units='M/M', sample_rate=20, angular_period=30), 'BS', True, 'BS'),
            (dict(sensor_type='tide', input_units='M', sample_rate=20, angular_period=30), 'BT', True, 'BT'),
            # Rain, bolometer, volumetric strain, wind: no dip/azimuth.
            (dict(sensor_type='rainfall', sample_rate=20, angular_period=30), 'BR', False, 'BR'),
            (dict(sensor_type='bolometer', sample_rate=20, angular_period=30), 'BU', False, 'BU'),
            (dict(input_units='M**3/M**3', sample_rate=20, angular_period=30), 'BV', False, 'BV'),
            (dict(sensor_type='wind', sample_rate=20, angular_period=30), 'BW', False, 'BWS'),
            (dict(sensor_type='wind', sample_rate=20, angular_period=30, description='direction'), 'BW', False, 'BWD'),
        )
        for kwargs, prefix, applies, code in cases:
            suggestion = suggest_channel_prefix(**kwargs)
            self.assertEqual(suggestion['prefix'], prefix, msg=kwargs)
            self.assertEqual(suggestion['orientationApplies'], applies, msg=kwargs)
            self.assertEqual(suggestion['code'], code, msg=kwargs)

    def test_partial_and_legacy(self):
        rate_only = suggest_channel_prefix(sample_rate=20)
        self.assertEqual(rate_only['prefix'], 'B')
        empty = suggest_channel_prefix()
        self.assertEqual(empty['prefix'], '')
        legacy = suggest_channel_prefix(sample_rate=20, legacy_instrument='L')
        self.assertEqual(legacy['prefix'], 'BL')

    def test_combined_response_rate_and_units_assume_broadband(self):
        class Stage(object):
            def __init__(self, input_units, input_rate, factor, output_rate=None):
                self.input_units = input_units
                self.decimation_input_sample_rate = input_rate
                self.decimation_factor = factor
                self.decimation_output_sample_rate = output_rate

        class Sensitivity(object):
            input_units = 'M/S'

        class Response(object):
            instrument_sensitivity = Sensitivity()
            response_stages = [Stage('M/S', 100, 1), Stage('V', 100, 1, 40)]

        rate, units = response_sample_rate_and_units(Response())
        self.assertEqual(rate, 40)
        self.assertEqual(units, 'M/S')
        suggestion = suggest_channel_prefix(
            sensor_type=None,
            angular_period=None,
            sample_rate=rate,
            input_units=units,
        )
        self.assertEqual(suggestion['prefix'], 'BH')

    def test_keys_and_resp(self):
        self.assertEqual(angular_period_from_keys(['120 s', 'STS-2']), 120)
        self.assertEqual(
            sample_rate_from_keys(['120 s'], ['100 Hz', 'causal']), 100
        )
        units, letter = units_and_legacy_from_resp(
            'B054F05     Response in units lookup:              M/S - Velocity\n'
            'B052F04     Channel:                               SHZ\n'
        )
        self.assertEqual(units, 'M/S')
        self.assertEqual(letter, 'H')
        self.assertEqual(
            input_units_from_text('Stage 1: PolesZerosResponseStage from M/S**2 to V, gain: 1'),
            'M/S**2'
        )

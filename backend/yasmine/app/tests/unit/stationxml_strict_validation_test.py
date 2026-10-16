# 2026-09-27, version 4.4.0-beta: ASGSR, Alexey Emanov
import inspect
import math
import unittest

from obspy import UTCDateTime
from obspy.core.inventory import Channel, Inventory, Network, Station
from obspy.core.inventory.response import (
    CoefficientsTypeResponseStage,
    FIRResponseStage,
    InstrumentSensitivity,
    PolesZerosResponseStage,
    Response,
)

from yasmine.app.utils.imp_exp import ExportStationXml, ExportUserLibrary
from yasmine.app.utils.stationxml_strict_validation import validate_inventory_strict


def _codes(inventory):
    return {item['code'] for item in validate_inventory_strict(inventory)}


def _channel(code='BHZ', latitude=55.0, longitude=82.0, elevation=100.0, depth=0.0,
             azimuth=0.0, dip=-90.0, sample_rate=40.0, response=None, **kwargs):
    return Channel(
        code=code,
        location_code=kwargs.pop('location_code', ''),
        latitude=latitude,
        longitude=longitude,
        elevation=elevation,
        depth=depth,
        azimuth=azimuth,
        dip=dip,
        sample_rate=sample_rate,
        response=response,
        **kwargs,
    )


def _inventory(channels, station_code='TEST', network_code='XX', **station_kwargs):
    station_kwargs.setdefault('latitude', 55.0)
    station_kwargs.setdefault('longitude', 82.0)
    station_kwargs.setdefault('elevation', 100.0)
    station = Station(code=station_code, channels=channels, **station_kwargs)
    network = Network(code=network_code, stations=[station])
    return Inventory(networks=[network], source='test')


def _normalization(poles, zeros, frequency):
    variable = 2j * math.pi * frequency
    numerator = 1 + 0j
    denominator = 1 + 0j
    for zero in zeros:
        numerator *= variable - zero
    for pole in poles:
        denominator *= variable - pole
    return 1.0 / abs(numerator / denominator)


def _velocity_response(frequency):
    poles = [-0.037 + 0.037j, -0.037 - 0.037j]
    zeros = [0j, 0j]
    stage = PolesZerosResponseStage(
        stage_sequence_number=1,
        stage_gain=1.0,
        stage_gain_frequency=frequency,
        input_units='M/S',
        output_units='V',
        pz_transfer_function_type='LAPLACE (RADIANS/SECOND)',
        normalization_frequency=frequency,
        zeros=zeros,
        poles=poles,
        normalization_factor=_normalization(poles, zeros, frequency),
    )
    sensitivity = InstrumentSensitivity(
        value=1.0,
        frequency=frequency,
        input_units='M/S',
        output_units='V',
    )
    return Response(response_stages=[stage], instrument_sensitivity=sensitivity)


class StrictValidationTest(unittest.TestCase):

    def test_flat_band_edges_stay_at_or_below_calibration(self):
        inventory = _inventory([_channel(response=_velocity_response(1.0))])
        codes = _codes(inventory)
        self.assertNotIn('strict.amplitude.eval_failed', codes)
        self.assertNotIn('strict.amplitude.edge_above_calibration', codes)
        self.assertNotIn('strict.amplitude.peak_above_calibration', codes)
        self.assertNotIn('strict.amplitude.stage_edge', codes)

    def test_high_frequency_edge_above_calibration_warns(self):
        inventory = _inventory([_channel(response=_velocity_response(0.001))])
        issues = validate_inventory_strict(inventory)
        matched = [
            item for item in issues
            if item['code'] == 'strict.amplitude.edge_above_calibration'
        ]
        self.assertTrue(matched)
        self.assertIn('times the calibration amplitude', matched[0]['message'])
        self.assertTrue(all(item['severity'] == 'warning' for item in issues))

    def test_overlapping_station_epochs_warn(self):
        first = Station(
            code='AAA', latitude=10.0, longitude=20.0, elevation=100.0,
            start_date=UTCDateTime('2020-01-01'), end_date=UTCDateTime('2021-01-01'),
        )
        second = Station(
            code='AAA', latitude=10.0, longitude=20.0, elevation=100.0,
            start_date=UTCDateTime('2020-06-01'), end_date=UTCDateTime('2021-06-01'),
        )
        inventory = Inventory(
            networks=[Network(code='XX', stations=[first, second])],
            source='test',
        )
        self.assertIn('strict.time.overlap', _codes(inventory))

    def test_closed_epoch_with_inverted_dates_still_warns(self):
        channel = _channel(
            start_date=UTCDateTime('2010-02-01'),
            end_date=UTCDateTime('2010-01-01'),
        )
        self.assertIn('strict.time.inverted', _codes(_inventory([channel])))

    def test_elevation_and_depth_convention_warns(self):
        channel = _channel(elevation=50.0, depth=0.0)
        self.assertIn('strict.geometry.elevation_convention', _codes(_inventory([channel])))

    def test_band_code_disagrees_with_sample_rate(self):
        channel = _channel(code='EHZ', sample_rate=40.0, azimuth=0.0, dip=-90.0)
        self.assertIn('strict.codes.band', _codes(_inventory([channel])))

    def test_accelerometer_high_frequency_poles_stay_broadband(self):
        # Force-balance poles around tens of Hz are bandwidth, not SEED corner.
        poles = [-314.0 + 0j, -314.0 + 0j]
        zeros = [0j, 0j, 0j]
        stage = PolesZerosResponseStage(
            stage_sequence_number=1,
            stage_gain=1.0,
            stage_gain_frequency=1.0,
            input_units='M/S**2',
            output_units='V',
            pz_transfer_function_type='LAPLACE (RADIANS/SECOND)',
            normalization_frequency=1.0,
            zeros=zeros,
            poles=poles,
            normalization_factor=_normalization(poles, zeros, 1.0),
        )
        response = Response(
            response_stages=[stage],
            instrument_sensitivity=InstrumentSensitivity(1.0, 1.0, 'M/S**2', 'V'),
        )
        channel = _channel(
            code='HNZ', sample_rate=100.0, azimuth=0.0, dip=-90.0, response=response,
        )
        self.assertNotIn('strict.codes.band', _codes(_inventory([channel])))

    def test_short_period_velocity_still_expects_e_band(self):
        poles = [-4.44 + 4.44j, -4.44 - 4.44j]
        zeros = [0j, 0j]
        stage = PolesZerosResponseStage(
            stage_sequence_number=1,
            stage_gain=1.0,
            stage_gain_frequency=1.0,
            input_units='M/S',
            output_units='V',
            pz_transfer_function_type='LAPLACE (RADIANS/SECOND)',
            normalization_frequency=1.0,
            zeros=zeros,
            poles=poles,
            normalization_factor=_normalization(poles, zeros, 1.0),
        )
        response = Response(
            response_stages=[stage],
            instrument_sensitivity=InstrumentSensitivity(1.0, 1.0, 'M/S', 'V'),
        )
        channel = _channel(
            code='HHZ', sample_rate=100.0, azimuth=0.0, dip=-90.0, response=response,
        )
        self.assertIn('strict.codes.band', _codes(_inventory([channel])))

    def test_unstable_pole_warns(self):
        stage = PolesZerosResponseStage(
            stage_sequence_number=1,
            stage_gain=1.0,
            stage_gain_frequency=1.0,
            input_units='M/S',
            output_units='V',
            pz_transfer_function_type='LAPLACE (RADIANS/SECOND)',
            normalization_frequency=1.0,
            zeros=[0j],
            poles=[0.1 + 0j],
            normalization_factor=1.0,
        )
        response = Response(
            response_stages=[stage],
            instrument_sensitivity=InstrumentSensitivity(1.0, 1.0, 'M/S', 'V'),
        )
        self.assertIn('strict.response.pole_stability', _codes(_inventory([_channel(response=response)])))

    def test_station_channel_distance_warns(self):
        channel = _channel(latitude=56.0, longitude=82.0)
        self.assertIn('strict.geometry.distance', _codes(_inventory([channel])))

    def test_horizontal_components_are_not_orthogonal(self):
        channels = [
            _channel(code='BHZ', azimuth=0.0, dip=-90.0),
            _channel(code='BHN', azimuth=0.0, dip=0.0),
            _channel(code='BHE', azimuth=0.0, dip=0.0),
        ]
        self.assertIn('strict.geometry.triplet_azimuth', _codes(_inventory(channels)))

    def test_fir_sum_far_from_one_warns(self):
        stage = FIRResponseStage(
            stage_sequence_number=1,
            stage_gain=1.0,
            stage_gain_frequency=1.0,
            input_units='V',
            output_units='count',
            symmetry='NONE',
            coefficients=[1.0, 1.0, 1.0, 1.0],
            decimation_input_sample_rate=40.0,
            decimation_factor=1,
            decimation_offset=0,
            decimation_delay=0.0,
            decimation_correction=0.0,
        )
        response = Response(
            response_stages=[stage],
            instrument_sensitivity=InstrumentSensitivity(1.0, 1.0, 'V', 'count'),
        )
        channel = _channel(code='BHZ', response=response)
        self.assertIn('strict.response.fir_sum', _codes(_inventory([channel])))

    def test_lowpass_fir_allows_zero_gain_frequency(self):
        stage = FIRResponseStage(
            stage_sequence_number=1,
            stage_gain=1.0,
            stage_gain_frequency=0.0,
            input_units='V',
            output_units='count',
            symmetry='NONE',
            coefficients=[0.25, 0.5, 0.25],
            decimation_input_sample_rate=40.0,
            decimation_factor=1,
            decimation_offset=0,
            decimation_delay=0.025,
            decimation_correction=0.025,
        )
        response = Response(
            response_stages=[stage],
            instrument_sensitivity=InstrumentSensitivity(1.0, 1.0, 'V', 'count'),
        )
        self.assertNotIn(
            'strict.response.stage_gain_frequency',
            _codes(_inventory([_channel(code='BHZ', response=response)])),
        )

    def test_unity_coefficients_allows_zero_gain_frequency(self):
        stage = CoefficientsTypeResponseStage(
            stage_sequence_number=1,
            stage_gain=1.0,
            stage_gain_frequency=0.0,
            input_units='V',
            output_units='count',
            cf_transfer_function_type='DIGITAL',
            numerator=[1.0],
            denominator=[1.0],
            decimation_input_sample_rate=40.0,
            decimation_factor=1,
            decimation_offset=0,
            decimation_delay=0.0,
            decimation_correction=0.0,
        )
        response = Response(
            response_stages=[stage],
            instrument_sensitivity=InstrumentSensitivity(1.0, 1.0, 'V', 'count'),
        )
        self.assertNotIn(
            'strict.response.stage_gain_frequency',
            _codes(_inventory([_channel(code='BHZ', response=response)])),
        )

    def test_poleszeros_zero_gain_frequency_warns(self):
        stage = PolesZerosResponseStage(
            stage_sequence_number=1,
            stage_gain=1.0,
            stage_gain_frequency=0.0,
            input_units='M/S',
            output_units='V',
            pz_transfer_function_type='LAPLACE (RADIANS/SECOND)',
            normalization_frequency=1.0,
            zeros=[0j],
            poles=[-1 + 0j],
            normalization_factor=1.0,
        )
        response = Response(
            response_stages=[stage],
            instrument_sensitivity=InstrumentSensitivity(1.0, 1.0, 'M/S', 'V'),
        )
        self.assertIn(
            'strict.response.stage_gain_frequency',
            _codes(_inventory([_channel(response=response)])),
        )

    def test_highpass_fir_zero_gain_frequency_warns(self):
        stage = FIRResponseStage(
            stage_sequence_number=1,
            stage_gain=1.0,
            stage_gain_frequency=0.0,
            input_units='V',
            output_units='count',
            symmetry='NONE',
            coefficients=[1.0, -1.0],
            decimation_input_sample_rate=40.0,
            decimation_factor=1,
            decimation_offset=0,
            decimation_delay=0.0125,
            decimation_correction=0.0125,
        )
        response = Response(
            response_stages=[stage],
            instrument_sensitivity=InstrumentSensitivity(1.0, 1.0, 'V', 'count'),
        )
        self.assertIn(
            'strict.response.stage_gain_frequency',
            _codes(_inventory([_channel(code='BHZ', response=response)])),
        )

    def test_progress_is_reported_for_every_channel(self):
        inventory = _inventory([
            _channel(code='BHZ'),
            _channel(code='BHN', azimuth=0.0, dip=0.0),
        ])
        seen = []

        def progress(done, total):
            seen.append((done, total))

        issues = validate_inventory_strict(inventory, progress=progress)
        self.assertEqual(seen, [(1, 2), (2, 2)])
        self.assertTrue(all(item['severity'] == 'warning' for item in issues))

    def test_channel_path_includes_epoch(self):
        inventory = _inventory([
            _channel(
                code='BHZ',
                start_date=UTCDateTime('2020-01-01'),
                end_date=UTCDateTime('2021-01-01'),
                latitude=56.0,
            ),
            _channel(
                code='BHZ',
                start_date=UTCDateTime('2022-01-01'),
                end_date=UTCDateTime('2023-01-01'),
                latitude=56.0,
            ),
        ])
        distance = [
            item for item in validate_inventory_strict(inventory)
            if item['code'] == 'strict.geometry.distance'
        ]
        paths = {item['path'] for item in distance}
        self.assertEqual(len(paths), 2)
        self.assertTrue(all('[' in path and ']' in path for path in paths))
        self.assertTrue(any('2020-01-01' in path for path in paths))
        self.assertTrue(any('2022-01-01' in path for path in paths))

    def test_triplet_warnings_are_keyed_by_epoch(self):
        channels = [
            _channel(
                code='BHZ', azimuth=0.0, dip=-90.0,
                start_date=UTCDateTime('2020-01-01'), end_date=UTCDateTime('2021-01-01'),
            ),
            _channel(
                code='BHN', azimuth=0.0, dip=0.0,
                start_date=UTCDateTime('2020-01-01'), end_date=UTCDateTime('2021-01-01'),
            ),
            _channel(
                code='BHE', azimuth=0.0, dip=0.0,
                start_date=UTCDateTime('2020-01-01'), end_date=UTCDateTime('2021-01-01'),
            ),
            _channel(
                code='BHZ', azimuth=0.0, dip=-90.0,
                start_date=UTCDateTime('2022-01-01'), end_date=UTCDateTime('2023-01-01'),
            ),
            _channel(
                code='BHN', azimuth=0.0, dip=0.0,
                start_date=UTCDateTime('2022-01-01'), end_date=UTCDateTime('2023-01-01'),
            ),
            _channel(
                code='BHE', azimuth=0.0, dip=0.0,
                start_date=UTCDateTime('2022-01-01'), end_date=UTCDateTime('2023-01-01'),
            ),
        ]
        azimuth = [
            item for item in validate_inventory_strict(_inventory(channels))
            if item['code'] == 'strict.geometry.triplet_azimuth'
        ]
        paths = {item['path'] for item in azimuth}
        self.assertEqual(len(paths), 2)
        self.assertTrue(all('BH*' in path for path in paths))
        self.assertTrue(any('2020-01-01' in path for path in paths))
        self.assertTrue(any('2022-01-01' in path for path in paths))
        self.assertNotIn('strict.geometry.triplet_epoch', _codes(_inventory(channels)))

    def test_triplet_compares_only_overlapping_epochs(self):
        channels = [
            _channel(
                code='BHZ', azimuth=0.0, dip=-90.0,
                start_date=UTCDateTime('2020-01-01'), end_date=UTCDateTime('2021-01-01'),
            ),
            _channel(
                code='BHN', azimuth=0.0, dip=0.0,
                start_date=UTCDateTime('2020-01-01'), end_date=UTCDateTime('2021-01-01'),
            ),
            _channel(
                code='BHE', azimuth=90.0, dip=0.0,
                start_date=UTCDateTime('2020-01-01'), end_date=UTCDateTime('2021-01-01'),
            ),
            _channel(
                code='BHZ', azimuth=0.0, dip=-90.0,
                start_date=UTCDateTime('2022-01-01'), end_date=UTCDateTime('2023-01-01'),
            ),
            _channel(
                code='BHN', azimuth=0.0, dip=0.0,
                start_date=UTCDateTime('2022-01-01'), end_date=UTCDateTime('2023-01-01'),
            ),
        ]
        codes = _codes(_inventory(channels))
        self.assertNotIn('strict.geometry.triplet_azimuth', codes)
        self.assertNotIn('strict.geometry.triplet_epoch', codes)
        incomplete = [
            item for item in validate_inventory_strict(_inventory(channels))
            if item['code'] == 'strict.geometry.triplet_incomplete'
        ]
        self.assertEqual(len(incomplete), 1)
        self.assertIn('2022-01-01', incomplete[0]['path'])
        self.assertNotIn('2020-01-01', incomplete[0]['path'])

    def test_triplet_sensor_replace_on_one_channel(self):
        channels = [
            _channel(
                code='BHZ', azimuth=0.0, dip=-90.0,
                start_date=UTCDateTime('2020-01-01'),
            ),
            _channel(
                code='BHN', azimuth=0.0, dip=0.0,
                start_date=UTCDateTime('2020-01-01'),
            ),
            _channel(
                code='BHE', azimuth=90.0, dip=0.0,
                start_date=UTCDateTime('2020-01-01'),
                end_date=UTCDateTime('2021-06-01'),
            ),
            _channel(
                code='BHE', azimuth=0.0, dip=0.0,
                start_date=UTCDateTime('2021-06-01'),
            ),
        ]
        issues = validate_inventory_strict(_inventory(channels))
        codes = {item['code'] for item in issues}
        self.assertIn('strict.geometry.triplet_epoch', codes)
        self.assertNotIn('strict.geometry.triplet_incomplete', codes)
        azimuth = [
            item for item in issues
            if item['code'] == 'strict.geometry.triplet_azimuth'
        ]
        self.assertEqual(len(azimuth), 1)
        self.assertIn('2021-06-01', azimuth[0]['path'])
        self.assertTrue(
            any(item['code'] == 'strict.geometry.triplet_epoch' for item in issues)
        )
    def test_scanner_emits_warnings_only(self):
        inventories = [
            _inventory([_channel(response=_velocity_response(0.001))]),
            _inventory([_channel(code='EHZ')]),
            _inventory([_channel(latitude=56.0)]),
        ]
        for inventory in inventories:
            issues = validate_inventory_strict(inventory)
            self.assertTrue(issues)
            self.assertTrue(all(item['severity'] == 'warning' for item in issues))

    def test_export_does_not_run_strict_checks(self):
        for method in (ExportStationXml.run, ExportUserLibrary.run):
            source = inspect.getsource(method)
            self.assertNotIn('validate_strict', source)
            self.assertNotIn('validate_inventory_strict', source)


if __name__ == '__main__':
    unittest.main()

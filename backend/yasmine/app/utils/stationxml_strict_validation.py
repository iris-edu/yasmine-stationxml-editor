# 2026-09-27, version 4.4.0-beta: ASGSR, Alexey Emanov
# ****************************************************************************
#
# Strict StationXML review. Every finding is a warning.
# This module is not used by export. Export stays limited to the
# StationXML 1.2 schema checks that already exist in the project.
#
# ****************************************************************************

import cmath
import gc
import math
import re

import numpy as np
from obspy import UTCDateTime

from yasmine.app.helpers.nrl.seed_channel_prefix import band_code


_AMPLITUDE_RATIO = 1.02
_SENSITIVITY_WARN = 0.01
_SENSITIVITY_FAIL = 0.05
_TRIPLET_SENSITIVITY = 0.05
_FIR_NORM_PASS = 0.005
_FIR_NORM_FAIL = 0.02
_FIR_SUM_NEAR_ZERO = 0.1
_GRID_SIZE = 80
_EARTH_RADIUS_M = 6371000.0
_ELEVATION_TOLERANCE_M = 5.0
_DISTANCE_M = 1000.0
_TRIPLET_DISTANCE_M = 10.0
_ORIENTATION_DEG = 5.0
_SHORT_EPOCH_SECONDS = 60.0
_GAP_SECONDS = 1.0
_SEED_UNIT_TOKENS = frozenset({
    'M/S', 'M/SEC', 'M/S**2', 'M/SEC**2', 'M/(S**2)', 'COUNTS', 'COUNT', 'M',
})
_SEISMOMETER_LETTERS = frozenset({'H', 'L', 'N', 'M'})
_LETTER_MOTION = {
    'H': 'velocity',
    'L': 'velocity',
    'N': 'acceleration',
    'M': 'displacement',
}
_OPEN_END = None


def validate_inventory_strict(inventory, progress=None):
    """Return warning dicts for suspicious StationXML content.

    Nothing returned here is an error, and nothing here blocks export.
    ``progress(done, total)`` runs after every channel. One failed channel
    does not discard warnings already collected.
    """
    issues = []
    now = UTCDateTime()
    serials = {}
    networks = list(getattr(inventory, 'networks', None) or [])
    total = 0
    for network in networks:
        for station in list(getattr(network, 'stations', None) or []):
            total += len(list(getattr(station, 'channels', None) or []))
    done = [0]

    def tick():
        done[0] += 1
        if done[0] % 250 == 0:
            gc.collect()
        if progress is None:
            return
        try:
            progress(done[0], total)
        except Exception:
            pass

    try:
        for network in networks:
            try:
                _scan_network(issues, network, now, serials, tick)
            except Exception as exc:
                _warn(
                    issues, 'response', 'strict.scan_failed',
                    _text(getattr(network, 'code', None)) or '/',
                    'Network checks could not be completed: %s' % exc,
                )
        _warn_duplicate_serials(issues, serials)
    except Exception as exc:
        _warn(
            issues, 'response', 'strict.scan_failed', '/',
            'Strict checks could not be completed: %s' % exc,
        )
    if progress is not None and total == 0:
        try:
            progress(1, 1)
        except Exception:
            pass
    return issues


def _warn(issues, category, code, path, message):
    issues.append({
        'severity': 'warning',
        'category': category,
        'code': code,
        'path': path or '/',
        'message': message,
    })


def _scan_network(issues, network, now, serials, tick=None):
    net_code = _text(getattr(network, 'code', None))
    net_path = net_code or '?'
    if not re.fullmatch(r'[A-Z0-9]{1,8}', net_code):
        _warn(
            issues, 'codes', 'strict.codes.network', net_path,
            "Network code '%s' should match [A-Z0-9] and be 1 to 8 characters" % net_code,
        )
    net_start = _utc(getattr(network, 'start_date', None))
    net_end = _utc(getattr(network, 'end_date', None))
    _check_epoch(issues, net_path, 'Network', net_start, net_end, now)
    _check_comments(issues, net_path, getattr(network, 'comments', None), net_start, net_end)

    stations = list(getattr(network, 'stations', None) or [])
    by_code = {}
    for station in stations:
        sta_code = _text(getattr(station, 'code', None))
        by_code.setdefault(sta_code, []).append(station)
        try:
            _scan_station(issues, network, station, net_start, net_end, now, serials, tick)
        except Exception as exc:
            _warn(
                issues, 'response', 'strict.scan_failed',
                _station_path(network, station),
                'Station checks could not be completed: %s' % exc,
            )
    for sta_code, group in by_code.items():
        _check_overlaps_and_gaps(
            issues,
            '%s.%s' % (net_path, sta_code or '?'),
            'Station %s' % (sta_code or '?'),
            [(sta_code, _utc(getattr(sta, 'start_date', None)), _utc(getattr(sta, 'end_date', None))) for sta in group],
        )


def _scan_station(issues, network, station, net_start, net_end, now, serials, tick=None):
    net_code = _text(getattr(network, 'code', None)) or '?'
    sta_code = _text(getattr(station, 'code', None))
    sta_start = _utc(getattr(station, 'start_date', None))
    sta_end = _utc(getattr(station, 'end_date', None))
    base_path = '%s.%s' % (net_code, sta_code or '?')
    path = _with_epoch(base_path, sta_start, sta_end)
    if not re.fullmatch(r'[A-Z0-9]{1,5}', sta_code):
        _warn(
            issues, 'codes', 'strict.codes.station', path,
            "Station code '%s' should match [A-Z0-9] and be 1 to 5 characters" % sta_code,
        )
    _check_epoch(issues, path, 'Station', sta_start, sta_end, now)
    _check_parent_epoch(issues, path, 'Station', 'network', net_start, net_end, sta_start, sta_end)
    _check_comments(issues, path, getattr(station, 'comments', None), sta_start, sta_end)
    _check_latitude_longitude(issues, path, 'Station', getattr(station, 'latitude', None), getattr(station, 'longitude', None))
    _check_elevation_range(issues, path, 'Station', getattr(station, 'elevation', None))

    channels = list(getattr(station, 'channels', None) or [])
    by_key = {}
    for channel in channels:
        cha_code = _text(getattr(channel, 'code', None))
        loc = _text(getattr(channel, 'location_code', None))
        by_key.setdefault((cha_code, loc), []).append(channel)
        try:
            _scan_channel(issues, network, station, channel, sta_start, sta_end, now, serials)
        except Exception as exc:
            _warn(
                issues, 'response', 'strict.channel.scan_failed',
                _channel_path(network, station, channel),
                'Channel checks could not be completed: %s' % exc,
            )
        finally:
            if tick is not None:
                tick()
    for (cha_code, loc), group in by_key.items():
        label = '%s.%s' % (cha_code or '?', loc or '--')
        _check_overlaps_and_gaps(
            issues,
            '%s.%s.%s' % (base_path, loc, cha_code or '?'),
            'Channel %s' % label,
            [(
                label,
                _utc(getattr(channel, 'start_date', None)),
                _utc(getattr(channel, 'end_date', None)),
            ) for channel in group],
        )
    _check_triplets(issues, network, station, channels)


def _scan_channel(issues, network, station, channel, sta_start, sta_end, now, serials):
    path = _channel_path(network, station, channel)
    code = _text(getattr(channel, 'code', None))
    location = _text(getattr(channel, 'location_code', None))
    if not re.fullmatch(r'[A-Z0-9]{3}', code):
        _warn(
            issues, 'codes', 'strict.codes.channel', path,
            "Channel code '%s' should be exactly 3 characters matching [A-Z0-9]" % code,
        )
    if location and not location.strip():
        _warn(
            issues, 'codes', 'strict.codes.location', path,
            'Location code is whitespace',
        )
    elif len(location) > 2:
        _warn(
            issues, 'codes', 'strict.codes.location', path,
            "Location code '%s' is longer than 2 characters" % location,
        )

    cha_start = _utc(getattr(channel, 'start_date', None))
    cha_end = _utc(getattr(channel, 'end_date', None))
    _check_epoch(issues, path, 'Channel', cha_start, cha_end, now)
    _check_parent_epoch(issues, path, 'Channel', 'station', sta_start, sta_end, cha_start, cha_end)
    _check_comments(issues, path, getattr(channel, 'comments', None), cha_start, cha_end)

    latitude = getattr(channel, 'latitude', None)
    longitude = getattr(channel, 'longitude', None)
    _check_latitude_longitude(issues, path, 'Channel', latitude, longitude)
    _check_elevation_range(issues, path, 'Channel', getattr(channel, 'elevation', None))
    depth = _float(getattr(channel, 'depth', None))
    if depth is not None and depth < 0:
        _warn(
            issues, 'geometry', 'strict.geometry.depth', path,
            'Channel depth %.3f m is negative' % depth,
        )
    _check_station_channel_geometry(issues, path, station, channel)
    _check_orientation(issues, path, channel)
    _check_clock_drift(issues, path, channel)

    sensor = getattr(channel, 'sensor', None)
    if sensor is not None:
        description = _text(getattr(sensor, 'description', None))
        if not description:
            _warn(
                issues, 'equipment', 'strict.equipment.sensor_description', path,
                'Sensor description is empty',
            )
        serial = _text(getattr(sensor, 'serial_number', None))
        if serial:
            net_code = _text(getattr(network, 'code', None)) or '?'
            sta_code = _text(getattr(station, 'code', None)) or '?'
            serials.setdefault(serial, set()).add((net_code, sta_code, path))

    response = getattr(channel, 'response', None)
    sample_rate = _channel_sample_rate(channel, response)
    if response is not None and (sample_rate is None or sample_rate <= 0):
        _warn(
            issues, 'response', 'strict.response.sample_rate', path,
            'Channel has a response but sample rate is %s' % sample_rate,
        )
    _check_band_and_instrument(issues, path, channel, response, sample_rate)
    if response is not None:
        _check_response(issues, path, channel, response, sample_rate)


def _check_band_and_instrument(issues, path, channel, response, sample_rate):
    code = _text(getattr(channel, 'code', None)).upper()
    if len(code) < 3 or sample_rate is None or sample_rate <= 0:
        return
    units = _response_input_units(response)
    period = _seed_corner_period(response, units)
    expected = band_code(sample_rate, period)
    if expected and code[0] != expected:
        _warn(
            issues, 'codes', 'strict.codes.band', path,
            "Channel band '%s' does not match sample rate %.6g Hz (expected %s)" % (
                code[0], sample_rate, expected,
            ),
        )
    letter = code[1]
    motion = _LETTER_MOTION.get(letter)
    if motion is None:
        return
    actual = _motion_from_units(units)
    if actual and actual != motion:
        _warn(
            issues, 'codes', 'strict.codes.instrument', path,
            "Instrument letter '%s' expects %s but input units '%s' look like %s" % (
                letter, motion, units, actual,
            ),
        )


def _check_response(issues, path, channel, response, sample_rate):
    stages = list(getattr(response, 'response_stages', None) or [])
    numbers = [getattr(stage, 'stage_sequence_number', None) for stage in stages]
    if stages and numbers != list(range(1, len(stages) + 1)):
        _warn(
            issues, 'response', 'strict.response.stage_sequence', path,
            'Response stage numbers should be 1..N without gaps, got %s' % numbers,
        )
    for index, stage in enumerate(stages):
        if index:
            _check_unit_chain(issues, path, stages[index - 1], stage, index + 1)
        _check_stage_units_spelling(issues, path, stage)
        _check_stage_gain(issues, path, stage)
        _check_stage_decimation(issues, path, stage)
        _check_poles_zeros(issues, path, stage)
        _check_fir(issues, path, stage)
    _check_decimation_chain(issues, path, stages)
    _check_sample_rate_decimation(issues, path, stages, sample_rate)

    sensitivity = getattr(response, 'instrument_sensitivity', None)
    polynomial = getattr(response, 'instrument_polynomial', None)
    if sensitivity is not None and polynomial is not None:
        _warn(
            issues, 'response', 'strict.response.sensitivity_and_polynomial', path,
            'Response has both InstrumentSensitivity and InstrumentPolynomial',
        )
    if sensitivity is not None:
        _check_sensitivity(issues, path, sensitivity, stages, sample_rate)
    _check_amplitude(issues, path, response, sample_rate)


def _check_sensitivity(issues, path, sensitivity, stages, sample_rate):
    value = _float(getattr(sensitivity, 'value', None))
    if value is None or value <= 0:
        _warn(
            issues, 'response', 'strict.response.sensitivity_value', path,
            'InstrumentSensitivity value %s should be positive' % value,
        )
    frequency = _float(getattr(sensitivity, 'frequency', None))
    if frequency is None or frequency <= 0:
        _warn(
            issues, 'response', 'strict.response.sensitivity_frequency', path,
            'InstrumentSensitivity frequency %s should be positive' % frequency,
        )
    elif sample_rate is not None and sample_rate > 0 and frequency >= sample_rate / 2.0:
        _warn(
            issues, 'response', 'strict.response.nyquist', path,
            'InstrumentSensitivity frequency %.6g Hz is not below Nyquist %.6g Hz' % (
                frequency, sample_rate / 2.0,
            ),
        )
    _check_unit_spelling(issues, path, getattr(sensitivity, 'input_units', None), 'InstrumentSensitivity input')
    _check_unit_spelling(issues, path, getattr(sensitivity, 'output_units', None), 'InstrumentSensitivity output')
    if frequency is not None and abs(frequency) < 1e-30 and _stages_have_origin_zero(stages):
        _warn(
            issues, 'response', 'strict.response.zero_frequency', path,
            'InstrumentSensitivity frequency is 0 while a zero sits at the origin',
        )


def _check_stage_gain(issues, path, stage):
    if _is_polynomial_stage(stage):
        return
    number = getattr(stage, 'stage_sequence_number', '?')
    if not hasattr(stage, 'stage_gain') and not hasattr(stage, 'stage_gain_frequency'):
        return
    gain = _float(getattr(stage, 'stage_gain', None))
    if gain is None or gain <= 0:
        _warn(
            issues, 'response', 'strict.response.stage_gain', path,
            'Stage %s gain %s should be positive' % (number, gain),
        )
    frequency = _float(getattr(stage, 'stage_gain_frequency', None))
    # FDSN prefers StageGain Frequency = 0 Hz for low-pass FIR (DC / sum of
    # coefficients). Other stages need a positive frequency in the passband.
    if frequency is None:
        _warn(
            issues, 'response', 'strict.response.stage_gain_frequency', path,
            'Stage %s gain frequency is missing' % number,
        )
    elif frequency < 0:
        _warn(
            issues, 'response', 'strict.response.stage_gain_frequency', path,
            'Stage %s gain frequency %.6g Hz should not be negative' % (number, frequency),
        )
    elif abs(frequency) < 1e-30:
        if not _is_lowpass_fir_stage(stage):
            _warn(
                issues, 'response', 'strict.response.stage_gain_frequency', path,
                'Stage %s gain frequency 0.0 is only preferred for low-pass FIR filters' % number,
            )
        if _stage_has_origin_zero(stage):
            _warn(
                issues, 'response', 'strict.response.zero_frequency', path,
                'Stage %s gain frequency is 0 while a zero sits at the origin' % number,
            )


def _check_unit_chain(issues, path, previous, current, number):
    left = _unit_key(getattr(previous, 'output_units', None))
    right = _unit_key(getattr(current, 'input_units', None))
    if left and right and left == right:
        return
    _warn(
        issues, 'response', 'strict.response.unit_chain', path,
        "Stage %s input units '%s' do not match the previous output '%s'" % (
            number,
            _raw_unit(getattr(current, 'input_units', None)),
            _raw_unit(getattr(previous, 'output_units', None)),
        ),
    )


def _check_stage_units_spelling(issues, path, stage):
    number = getattr(stage, 'stage_sequence_number', '?')
    _check_unit_spelling(issues, path, getattr(stage, 'input_units', None), 'Stage %s input' % number)
    _check_unit_spelling(issues, path, getattr(stage, 'output_units', None), 'Stage %s output' % number)


def _check_unit_spelling(issues, path, value, label):
    token = _raw_unit(value)
    if token in _SEED_UNIT_TOKENS:
        _warn(
            issues, 'response', 'strict.response.seed_units', path,
            "%s units '%s' should use the SI name (m/s, m/s**2, m, or count)" % (label, token),
        )


def _check_stage_decimation(issues, path, stage):
    if not _is_digital_stage(stage):
        return
    number = getattr(stage, 'stage_sequence_number', '?')
    rate = _float(getattr(stage, 'decimation_input_sample_rate', None))
    factor = _float(getattr(stage, 'decimation_factor', None))
    if rate is None or factor is None:
        _warn(
            issues, 'response', 'strict.response.decimation_missing', path,
            'Digital stage %s should include decimation input sample rate and factor' % number,
        )
        return
    if rate <= 0 or factor < 1:
        _warn(
            issues, 'response', 'strict.response.decimation_factor', path,
            'Stage %s decimation input sample rate %.6g and factor %.6g should be positive, with factor >= 1' % (
                number, rate, factor,
            ),
        )


def _check_decimation_chain(issues, path, stages):
    previous = None
    for stage in stages:
        rate = _float(getattr(stage, 'decimation_input_sample_rate', None))
        factor = _float(getattr(stage, 'decimation_factor', None))
        if rate is None or factor is None or factor == 0:
            continue
        if previous is not None and abs(previous - rate) > 1e-6:
            number = getattr(stage, 'stage_sequence_number', '?')
            _warn(
                issues, 'response', 'strict.response.decimation_chain', path,
                'Stage %s decimation input %.6g Hz does not match the previous output %.6g Hz' % (
                    number, rate, previous,
                ),
            )
        previous = rate / factor


def _check_sample_rate_decimation(issues, path, stages, sample_rate):
    if sample_rate is None or sample_rate <= 0:
        return
    expected = None
    for stage in reversed(stages):
        rate = _float(getattr(stage, 'decimation_input_sample_rate', None))
        factor = _float(getattr(stage, 'decimation_factor', None))
        if rate is None or factor in (None, 0):
            continue
        expected = rate / factor
        break
    if expected is None:
        return
    if abs(float(sample_rate) - expected) > 1e-6:
        _warn(
            issues, 'response', 'strict.response.sample_rate_decimation', path,
            'Channel sample rate %.6g Hz does not match the last decimation output %.6g Hz' % (
                sample_rate, expected,
            ),
        )


def _check_poles_zeros(issues, path, stage):
    if not hasattr(stage, 'poles') and not hasattr(stage, 'pz_transfer_function_type'):
        return
    number = getattr(stage, 'stage_sequence_number', '?')
    poles = list(getattr(stage, 'poles', None) or [])
    zeros = list(getattr(stage, 'zeros', None) or [])
    pz_type = str(getattr(stage, 'pz_transfer_function_type', '') or '')
    kind = pz_type.upper()
    digital = 'DIGITAL' in kind
    for index, pole in enumerate(poles):
        real, imag = _re_im(pole)
        if digital:
            radius = math.hypot(real, imag)
            if radius >= 1.0 + 1e-10:
                _warn(
                    issues, 'response', 'strict.response.pole_stability', path,
                    'Stage %s pole %s has magnitude %.6g outside the unit circle' % (number, index, radius),
                )
        elif real > 1e-10:
            _warn(
                issues, 'response', 'strict.response.pole_stability', path,
                'Stage %s pole %s has real part %.6g > 0 (unstable)' % (number, index, real),
            )
    _check_conjugates(issues, path, number, 'pole', poles)
    _check_conjugates(issues, path, number, 'zero', zeros)
    if not digital and len(zeros) > len(poles):
        _warn(
            issues, 'response', 'strict.response.rising_shape', path,
            'Stage %s has %s zeros and %s poles, so the amplitude can rise with frequency' % (
                number, len(zeros), len(poles),
            ),
        )
    a0 = _float(getattr(stage, 'normalization_factor', None))
    norm = _float(getattr(stage, 'normalization_frequency', None))
    if norm is not None and norm < 0:
        _warn(
            issues, 'response', 'strict.response.normalization_frequency', path,
            'Stage %s normalization frequency %.6g Hz is negative' % (number, norm),
        )
    if a0 is not None and a0 <= 0:
        _warn(
            issues, 'response', 'strict.response.a0', path,
            'Stage %s normalization factor %.6g should be positive' % (number, a0),
        )
    elif a0 is not None and norm is not None and norm > 0:
        sample_rate = _float(getattr(stage, 'decimation_input_sample_rate', None))
        value = _pz_response(poles, zeros, a0, norm, pz_type, sample_rate)
        if value is None:
            _warn(
                issues, 'response', 'strict.response.a0', path,
                'Stage %s A0 normalization could not be evaluated at %.6g Hz' % (number, norm),
            )
        elif abs(abs(value) - 1.0) > 0.01:
            _warn(
                issues, 'response', 'strict.response.a0', path,
                'Stage %s |H(fn)| is %.6g at %.6g Hz, expected 1 within 1%% (A0=%s)' % (
                    number, abs(value), norm, a0,
                ),
            )
    _check_stage_amplitude_edges(issues, path, stage, poles, zeros, a0, norm, pz_type)


def _check_conjugates(issues, path, number, name, roots):
    for index, root in enumerate(roots):
        real, imag = _re_im(root)
        if abs(imag) <= 1e-12:
            continue
        found = False
        for other_index, other in enumerate(roots):
            if other_index == index:
                continue
            other_real, other_imag = _re_im(other)
            if abs(other_real - real) < 1e-9 and abs(other_imag + imag) < 1e-9:
                found = True
                break
        if not found:
            _warn(
                issues, 'response', 'strict.response.conjugate', path,
                'Stage %s %s %s has no conjugate partner' % (number, name, index),
            )


def _check_stage_amplitude_edges(issues, path, stage, poles, zeros, a0, norm, pz_type):
    if a0 is None or a0 <= 0 or norm is None or norm <= 0:
        return
    number = getattr(stage, 'stage_sequence_number', '?')
    sample_rate = _float(getattr(stage, 'decimation_input_sample_rate', None))
    f_lo = max(1e-5, norm / 1000.0)
    if sample_rate is not None and sample_rate > 0:
        f_hi = 0.99 * sample_rate / 2.0
    else:
        f_hi = 100.0 * norm
    center = _pz_response(poles, zeros, a0, norm, pz_type, sample_rate)
    if center is None or abs(center) <= 0:
        return
    amp_center = abs(center)
    for label, freq in (('low-frequency end', f_lo), ('high-frequency end', f_hi)):
        if freq <= 0 or abs(freq - norm) / norm < 1e-6:
            continue
        value = _pz_response(poles, zeros, a0, freq, pz_type, sample_rate)
        if value is None:
            continue
        amp = abs(value)
        if amp > amp_center * _AMPLITUDE_RATIO:
            _warn(
                issues, 'amplitude', 'strict.amplitude.stage_edge', path,
                'Stage %s %s amplitude %.6g at %.6g Hz is %.3g times the amplitude %.6g at normalization %.6g Hz' % (
                    number, label, amp, freq, amp / amp_center, amp_center, norm,
                ),
            )


def _check_fir(issues, path, stage):
    coeffs = _fir_coefficients(stage)
    if coeffs is None:
        return
    number = getattr(stage, 'stage_sequence_number', '?')
    if stage.__class__.__name__ == 'FIRResponseStage' and len(coeffs) < 4:
        _warn(
            issues, 'response', 'strict.response.fir_length', path,
            'Stage %s FIR has only %s coefficients' % (number, len(coeffs)),
        )
    total = float(sum(coeffs))
    if abs(total) >= _FIR_SUM_NEAR_ZERO:
        deviation = abs(total - 1.0)
        if deviation > _FIR_NORM_FAIL:
            limit = '2%'
        elif deviation > _FIR_NORM_PASS:
            limit = '0.5%'
        else:
            limit = None
        if limit:
            _warn(
                issues, 'response', 'strict.response.fir_sum', path,
                'Stage %s FIR coefficient sum is %.6g (|sum-1|=%.4g, above %s)' % (
                    number, total, deviation, limit,
                ),
            )
    rate = _float(getattr(stage, 'decimation_input_sample_rate', None))
    if rate is not None and rate > 0 and len(coeffs) > 1:
        expected = (len(coeffs) - 1) / (2.0 * rate)
        tolerance = max(1e-6, 0.001 * expected, 0.001)
        delay = _float(getattr(stage, 'decimation_delay', None))
        correction = _float(getattr(stage, 'decimation_correction', None))
        if delay is not None and abs(delay - expected) > tolerance:
            _warn(
                issues, 'response', 'strict.response.fir_delay', path,
                'Stage %s decimation delay %.6g s is not (n-1)/(2*fs)=%.6g s' % (
                    number, delay, expected,
                ),
            )
        if correction is not None and abs(correction - expected) > tolerance:
            _warn(
                issues, 'response', 'strict.response.fir_delay', path,
                'Stage %s decimation correction %.6g s is not (n-1)/(2*fs)=%.6g s' % (
                    number, correction, expected,
                ),
            )
        _check_fir_edges(issues, path, number, coeffs, rate, stage)


def _check_fir_edges(issues, path, number, coeffs, sample_rate, stage):
    gain_frequency = _float(getattr(stage, 'stage_gain_frequency', None))
    if gain_frequency is None or gain_frequency <= 0:
        return
    try:
        values = np.asarray(coeffs, dtype=float)
        nfft = max(256, int(2 ** np.ceil(np.log2(max(values.size * 8, 16)))))
        spectrum = np.abs(np.fft.rfft(values, n=nfft))
        freqs = np.fft.rfftfreq(nfft, d=1.0 / float(sample_rate))
        center_index = int(np.argmin(np.abs(freqs - gain_frequency)))
        amp_center = float(spectrum[center_index])
        if not np.isfinite(amp_center) or amp_center <= 0:
            return
        points = []
        if spectrum.size > 2:
            points.append(('low-frequency end', float(freqs[1]), float(spectrum[1])))
        points.append(('high-frequency end', float(freqs[-1]), float(spectrum[-1])))
        for label, freq, amp in points:
            if amp > amp_center * _AMPLITUDE_RATIO:
                _warn(
                    issues, 'amplitude', 'strict.amplitude.fir_edge', path,
                    'Stage %s FIR %s amplitude %.6g at %.6g Hz is %.3g times the amplitude %.6g at gain frequency %.6g Hz' % (
                        number, label, amp, freq, amp / amp_center, amp_center, gain_frequency,
                    ),
                )
    except Exception as exc:
        _warn(
            issues, 'amplitude', 'strict.amplitude.eval_failed', path,
            'Stage %s FIR amplitude could not be compared: %s' % (number, exc),
        )


def _check_amplitude(issues, path, response, sample_rate):
    stages = list(getattr(response, 'response_stages', None) or [])
    if not stages and getattr(response, 'instrument_sensitivity', None) is None:
        return
    frequency = _calibration_frequency(response)
    if frequency is None:
        _warn(
            issues, 'amplitude', 'strict.amplitude.missing_calibration_frequency', path,
            'No positive calibration frequency on InstrumentSensitivity or the first stage',
        )
        return
    f_lo = max(1e-5, frequency / 1000.0)
    if sample_rate is not None and sample_rate > 0:
        f_hi = 0.99 * float(sample_rate) / 2.0
    else:
        f_hi = 100.0 * frequency
    if f_hi <= f_lo:
        _warn(
            issues, 'amplitude', 'strict.amplitude.eval_failed', path,
            'Amplitude grid is empty between %.6g Hz and %.6g Hz' % (f_lo, f_hi),
        )
        return
    try:
        grid = np.unique(np.concatenate([
            np.logspace(np.log10(f_lo), np.log10(f_hi), _GRID_SIZE),
            np.array([f_lo, f_hi, frequency], dtype=float),
        ]))
        values = response.get_evalresp_response_for_frequencies(grid, output='DEF')
        amps = np.abs(np.asarray(values, dtype=complex))
    except Exception as exc:
        _warn(
            issues, 'amplitude', 'strict.amplitude.eval_failed', path,
            'Response amplitude could not be evaluated: %s' % _short(exc),
        )
        return
    if amps.shape != grid.shape or not np.isfinite(amps).all():
        _warn(
            issues, 'amplitude', 'strict.amplitude.eval_failed', path,
            'Response amplitude was not finite on the check grid',
        )
        return
    amp_cal = float(amps[int(np.argmin(np.abs(grid - frequency)))])
    amp_lo = float(amps[int(np.argmin(np.abs(grid - f_lo)))])
    amp_hi = float(amps[int(np.argmin(np.abs(grid - f_hi)))])
    if not np.isfinite(amp_cal) or amp_cal <= 0:
        _warn(
            issues, 'amplitude', 'strict.amplitude.eval_failed', path,
            'Amplitude at calibration frequency %.6g Hz is %s' % (frequency, amp_cal),
        )
        return
    for label, freq, amp in (
        ('low-frequency end', f_lo, amp_lo),
        ('high-frequency end', f_hi, amp_hi),
    ):
        if amp > amp_cal * _AMPLITUDE_RATIO:
            _warn(
                issues, 'amplitude', 'strict.amplitude.edge_above_calibration', path,
                '%s amplitude %.6g at %.6g Hz is %.3g times the calibration amplitude %.6g at %.6g Hz' % (
                    label[0].upper() + label[1:], amp, freq, amp / amp_cal, amp_cal, frequency,
                ),
            )
    peak_index = int(np.argmax(amps))
    peak_amp = float(amps[peak_index])
    peak_freq = float(grid[peak_index])
    if abs(peak_freq - frequency) / frequency > 1e-6 and peak_amp > amp_cal * _AMPLITUDE_RATIO:
        _warn(
            issues, 'amplitude', 'strict.amplitude.peak_above_calibration', path,
            'Peak amplitude %.6g at %.6g Hz is %.3g times the calibration amplitude %.6g at %.6g Hz' % (
                peak_amp, peak_freq, peak_amp / amp_cal, amp_cal, frequency,
            ),
        )
    sensitivity = getattr(response, 'instrument_sensitivity', None)
    stated = _float(getattr(sensitivity, 'value', None)) if sensitivity is not None else None
    if stated is not None and stated > 0:
        relative = abs(amp_cal - stated) / stated
        if relative > _SENSITIVITY_FAIL:
            limit = '5%'
        elif relative > _SENSITIVITY_WARN:
            limit = '1%'
        else:
            limit = None
        if limit:
            _warn(
                issues, 'amplitude', 'strict.amplitude.sensitivity_mismatch', path,
                'Amplitude %.6g at %.6g Hz differs from InstrumentSensitivity %.6g by %.2f%% (above %s)' % (
                    amp_cal, frequency, stated, relative * 100.0, limit,
                ),
            )


def _check_triplets(issues, network, station, channels):
    seismic = []
    for channel in channels:
        code = _text(getattr(channel, 'code', None)).upper()
        if len(code) == 3 and code[1] in _SEISMOMETER_LETTERS:
            seismic.append(channel)
    clusters = {}
    for channel in seismic:
        code = _text(getattr(channel, 'code', None)).upper()
        key = (
            _text(getattr(channel, 'location_code', None)),
            code[:2],
        )
        clusters.setdefault(key, []).append(channel)
    net_code = _text(getattr(network, 'code', None)) or '?'
    sta_code = _text(getattr(station, 'code', None)) or '?'
    for (location, prefix), group in clusters.items():
        base_path = '%s.%s.%s.%s*' % (net_code, sta_code, location, prefix)
        _warn_triplet_epoch_mismatch(issues, base_path, group)
        for win_start, win_end, active in _triplet_windows(group):
            path = _with_epoch(
                base_path,
                _label_bound(win_start),
                _label_bound(win_end),
            )
            letters = set()
            for channel in active:
                code = _text(getattr(channel, 'code', None)).upper()
                if len(code) == 3:
                    letters.add(code[2])
            if letters & set('12'):
                expected = ('Z', '1', '2')
            elif letters & set('ZNE'):
                expected = ('Z', 'N', 'E')
            else:
                expected = ()
            missing = [letter for letter in expected if letter not in letters]
            if missing:
                _warn(
                    issues, 'geometry', 'strict.geometry.triplet_incomplete', path,
                    '%s triplet at location %s is missing %s' % (
                        prefix, location or '--', ', '.join(missing),
                    ),
                )
            _check_triplet_rates(issues, path, active)
            _check_triplet_positions(issues, path, active)
            _check_triplet_horizontals(issues, path, active)


def _warn_triplet_epoch_mismatch(issues, base_path, group):
    for index, left in enumerate(group):
        for right in group[index + 1:]:
            if _epoch_key(left) == _epoch_key(right):
                continue
            left_start = _utc(getattr(left, 'start_date', None))
            left_end = _utc(getattr(left, 'end_date', None))
            right_start = _utc(getattr(right, 'start_date', None))
            right_end = _utc(getattr(right, 'end_date', None))
            if not _epochs_overlap(left_start, left_end, right_start, right_end):
                continue
            inter_start, inter_end = _epoch_intersection(
                left_start, left_end, right_start, right_end,
            )
            _warn(
                issues, 'geometry', 'strict.geometry.triplet_epoch',
                _with_epoch(base_path, inter_start, inter_end),
                '%s epoch %s and %s epoch %s overlap but do not match' % (
                    _text(getattr(left, 'code', None)),
                    _epoch_label(left_start, left_end),
                    _text(getattr(right, 'code', None)),
                    _epoch_label(right_start, right_end),
                ),
            )


def _check_triplet_rates(issues, path, group):
    rates = []
    for channel in group:
        rate = _float(getattr(channel, 'sample_rate', None))
        if rate is not None:
            rates.append((channel, rate))
    for index, (left, left_rate) in enumerate(rates):
        for right, right_rate in rates[index + 1:]:
            if abs(left_rate - right_rate) > 1e-6:
                _warn(
                    issues, 'geometry', 'strict.geometry.triplet_rate', path,
                    'Sample rate %.6g Hz on %s differs from %.6g Hz on %s' % (
                        left_rate, _text(getattr(left, 'code', None)),
                        right_rate, _text(getattr(right, 'code', None)),
                    ),
                )
                return


def _check_triplet_positions(issues, path, group):
    for index, left in enumerate(group):
        for right in group[index + 1:]:
            try:
                distance = _horizontal_m(
                    float(left.latitude), float(left.longitude),
                    float(right.latitude), float(right.longitude),
                )
            except (TypeError, ValueError):
                continue
            if distance > _TRIPLET_DISTANCE_M:
                _warn(
                    issues, 'geometry', 'strict.geometry.triplet_position', path,
                    '%s and %s are %.0f m apart' % (
                        _text(getattr(left, 'code', None)),
                        _text(getattr(right, 'code', None)),
                        distance,
                    ),
                )
                return


def _check_triplet_horizontals(issues, path, group):
    by_letter = {}
    for channel in group:
        code = _text(getattr(channel, 'code', None)).upper()
        if len(code) == 3:
            by_letter.setdefault(code[2], []).append(channel)
    for left_letter, right_letter in (('N', 'E'), ('1', '2')):
        for left in by_letter.get(left_letter, []):
            for right in by_letter.get(right_letter, []):
                _compare_horizontal_pair(issues, path, left, right)


def _compare_horizontal_pair(issues, path, left, right):
    left_az = _float(getattr(left, 'azimuth', None))
    right_az = _float(getattr(right, 'azimuth', None))
    if left_az is not None and right_az is not None:
        separation = _angle_separation(left_az, right_az)
        if abs(separation - 90.0) > _ORIENTATION_DEG:
            _warn(
                issues, 'geometry', 'strict.geometry.triplet_azimuth', path,
                '%s azimuth %.1f° and %s azimuth %.1f° are %.1f° apart, expected about 90°' % (
                    _text(getattr(left, 'code', None)), left_az,
                    _text(getattr(right, 'code', None)), right_az,
                    separation,
                ),
            )
    left_gain = _sensitivity_value(left)
    right_gain = _sensitivity_value(right)
    if left_gain and right_gain:
        scale = max(abs(left_gain), abs(right_gain))
        if scale and abs(left_gain - right_gain) / scale > _TRIPLET_SENSITIVITY:
            _warn(
                issues, 'geometry', 'strict.geometry.triplet_sensitivity', path,
                '%s sensitivity %.6g and %s sensitivity %.6g differ by more than 5%%' % (
                    _text(getattr(left, 'code', None)), left_gain,
                    _text(getattr(right, 'code', None)), right_gain,
                ),
            )


def _check_orientation(issues, path, channel):
    code = _text(getattr(channel, 'code', None)).upper()
    if len(code) < 3 or code[1] not in _SEISMOMETER_LETTERS:
        return
    azimuth = _float(getattr(channel, 'azimuth', None))
    dip = _float(getattr(channel, 'dip', None))
    if azimuth is None or dip is None:
        _warn(
            issues, 'geometry', 'strict.geometry.missing_orientation', path,
            'Seismometer channel %s needs both azimuth and dip' % code,
        )
        return
    if azimuth < 0 or azimuth > 360:
        _warn(
            issues, 'geometry', 'strict.geometry.orientation', path,
            'Azimuth %.3f° is outside 0..360' % azimuth,
        )
    if dip < -90 or dip > 90:
        _warn(
            issues, 'geometry', 'strict.geometry.orientation', path,
            'Dip %.3f° is outside -90..90' % dip,
        )
    letter = code[2]
    if letter == 'Z' and not (_near_zero_azimuth(azimuth) and _near_vertical(dip)):
        _warn(
            issues, 'geometry', 'strict.geometry.orientation', path,
            'Z orientation expects azimuth near 0° and dip near ±90°, got azimuth %.1f° dip %.1f°' % (
                azimuth, dip,
            ),
        )
    elif letter == 'N' and not (_near_cardinal(azimuth, (0, 180)) and abs(dip) <= _ORIENTATION_DEG):
        _warn(
            issues, 'geometry', 'strict.geometry.orientation', path,
            'N orientation expects azimuth near 0° or 180° and dip near 0°, got azimuth %.1f° dip %.1f°' % (
                azimuth, dip,
            ),
        )
    elif letter == 'E' and not (_near_cardinal(azimuth, (90, 270)) and abs(dip) <= _ORIENTATION_DEG):
        _warn(
            issues, 'geometry', 'strict.geometry.orientation', path,
            'E orientation expects azimuth near 90° or 270° and dip near 0°, got azimuth %.1f° dip %.1f°' % (
                azimuth, dip,
            ),
        )


def _check_station_channel_geometry(issues, path, station, channel):
    try:
        sta_lat = float(station.latitude)
        sta_lon = float(station.longitude)
        cha_lat = float(channel.latitude)
        cha_lon = float(channel.longitude)
    except (TypeError, ValueError, AttributeError):
        return
    distance = _horizontal_m(sta_lat, sta_lon, cha_lat, cha_lon)
    if distance > _DISTANCE_M:
        _warn(
            issues, 'geometry', 'strict.geometry.distance', path,
            'Station to channel horizontal distance is %.0f m, above 1 km' % distance,
        )
    sta_elev = _float(getattr(station, 'elevation', None))
    cha_elev = _float(getattr(channel, 'elevation', None))
    depth = _float(getattr(channel, 'depth', None))
    if sta_elev is not None and cha_elev is not None and abs(sta_elev - cha_elev) > _DISTANCE_M:
        _warn(
            issues, 'geometry', 'strict.geometry.elevation_difference', path,
            'Station elevation %.1f m and channel elevation %.1f m differ by more than 1 km' % (
                sta_elev, cha_elev,
            ),
        )
    if sta_elev is None or cha_elev is None or depth is None:
        return
    buried = abs(sta_elev - cha_elev - depth) <= _ELEVATION_TOLERANCE_M
    same_surface = abs(sta_elev - cha_elev) <= _ELEVATION_TOLERANCE_M and depth >= 0
    if not buried and not same_surface:
        _warn(
            issues, 'geometry', 'strict.geometry.elevation_convention', path,
            'Elevations do not match burial (station %.1f, channel %.1f, depth %.1f) or a shared surface within 5 m' % (
                sta_elev, cha_elev, depth,
            ),
        )


def _check_latitude_longitude(issues, path, label, latitude, longitude):
    lat = _float(latitude)
    lon = _float(longitude)
    if lat is not None and (lat < -90 or lat > 90):
        _warn(
            issues, 'geometry', 'strict.geometry.latitude', path,
            '%s latitude %.4f is outside -90..90' % (label, lat),
        )
    if lon is not None and (lon < -180 or lon > 180):
        _warn(
            issues, 'geometry', 'strict.geometry.longitude', path,
            '%s longitude %.4f is outside -180..180' % (label, lon),
        )
    if lat == 0 and lon == 0:
        _warn(
            issues, 'geometry', 'strict.geometry.null_island', path,
            '%s latitude and longitude are both 0' % label,
        )


def _check_elevation_range(issues, path, label, elevation):
    value = _float(elevation)
    if value is None:
        return
    if value < -500 or value > 9000:
        _warn(
            issues, 'geometry', 'strict.geometry.elevation', path,
            '%s elevation %.1f m is outside -500..9000 m' % (label, value),
        )


def _check_clock_drift(issues, path, channel):
    drift = _float(getattr(channel, 'clock_drift_in_seconds_per_sample', None))
    if drift is None:
        return
    sample_rate = _float(getattr(channel, 'sample_rate', None))
    if drift < 0:
        _warn(
            issues, 'time', 'strict.time.clock_drift', path,
            'Clock drift %.6g s/sample is negative' % drift,
        )
    elif sample_rate is not None and sample_rate > 0 and drift > 1.0 / sample_rate:
        _warn(
            issues, 'time', 'strict.time.clock_drift', path,
            'Clock drift %.6g s/sample is larger than the sample period %.6g s' % (
                drift, 1.0 / sample_rate,
            ),
        )


def _check_epoch(issues, path, label, start, end, now):
    if start is not None and end is not None:
        if start > end:
            _warn(
                issues, 'time', 'strict.time.inverted', path,
                '%s start %s is after end %s' % (label, start, end),
            )
        elif start == end:
            _warn(
                issues, 'time', 'strict.time.zero_length', path,
                '%s start and end are both %s' % (label, start),
            )
        elif float(end - start) < _SHORT_EPOCH_SECONDS:
            _warn(
                issues, 'time', 'strict.time.short', path,
                '%s epoch is shorter than one minute (%s to %s)' % (label, start, end),
            )
    if end is not None and end > now:
        _warn(
            issues, 'time', 'strict.time.future_end', path,
            '%s end %s is in the future' % (label, end),
        )


def _check_parent_epoch(issues, path, label, parent_label, parent_start, parent_end, start, end):
    if parent_start is not None and start is not None and start < parent_start:
        _warn(
            issues, 'time', 'strict.time.parent', path,
            '%s starts at %s, before the %s start %s' % (label, start, parent_label, parent_start),
        )
    if parent_end is not None and end is not None and end > parent_end:
        _warn(
            issues, 'time', 'strict.time.parent', path,
            '%s ends at %s, after the %s end %s' % (label, end, parent_label, parent_end),
        )
    if parent_end is not None and end is None and (start is None or start < parent_end):
        _warn(
            issues, 'time', 'strict.time.parent', path,
            '%s is still open after the %s end %s' % (label, parent_label, parent_end),
        )
    if parent_end is not None and start is not None and start > parent_end:
        _warn(
            issues, 'time', 'strict.time.parent', path,
            '%s starts at %s, after the %s end %s' % (label, start, parent_label, parent_end),
        )


def _check_overlaps_and_gaps(issues, path, label, epochs):
    parsed = [(name, start, end) for name, start, end in epochs if start is not None]
    for index, (_, start_a, end_a) in enumerate(parsed):
        for _, start_b, end_b in parsed[index + 1:]:
            if _epochs_overlap(start_a, end_a, start_b, end_b):
                _warn(
                    issues, 'time', 'strict.time.overlap', path,
                    '%s epochs overlap (%s–%s and %s–%s)' % (
                        label, start_a, end_a or 'open', start_b, end_b or 'open',
                    ),
                )
                break
    ordered = sorted(parsed, key=lambda item: item[1])
    for (_, _, end_a), (_, start_b, _) in zip(ordered, ordered[1:]):
        if end_a is not None and float(start_b - end_a) > _GAP_SECONDS:
            _warn(
                issues, 'time', 'strict.time.gap', path,
                '%s epochs have a gap from %s to %s' % (label, end_a, start_b),
            )


def _check_comments(issues, path, comments, start, end):
    for index, comment in enumerate(list(comments or [])):
        begin = _utc(getattr(comment, 'begin_effective_time', None))
        finish = _utc(getattr(comment, 'end_effective_time', None))
        comment_path = '%s comment %s' % (path, index + 1)
        if begin is not None and finish is not None and begin >= finish:
            _warn(
                issues, 'time', 'strict.time.inverted', comment_path,
                'Comment effective time starts at %s and ends at %s' % (begin, finish),
            )
        outside = (
            (begin is not None and start is not None and begin < start)
            or (finish is not None and end is not None and finish > end)
            or (begin is not None and end is not None and begin > end)
            or (finish is not None and start is not None and finish < start)
        )
        if outside:
            _warn(
                issues, 'time', 'strict.time.comment', comment_path,
                'Comment effective time %s–%s falls outside the node epoch' % (
                    begin or 'open', finish or 'open',
                ),
            )


def _warn_duplicate_serials(issues, serials):
    for serial, places in serials.items():
        stations = {(net, sta) for net, sta, _path in places}
        if len(stations) < 2:
            continue
        listed = ', '.join(sorted('%s.%s' % pair for pair in stations))
        for _net, _sta, path in sorted(places):
            _warn(
                issues, 'equipment', 'strict.equipment.duplicate_serial', path,
                "Sensor serial '%s' is used at %s" % (serial, listed),
            )


_EPOCH_OPEN_START = UTCDateTime(0)
_EPOCH_OPEN_END = UTCDateTime('9999-12-31T23:59:59Z')


def _epochs_overlap(start_a, end_a, start_b, end_b):
    begin_a = start_a if start_a is not None else _EPOCH_OPEN_START
    begin_b = start_b if start_b is not None else _EPOCH_OPEN_START
    finish_a = end_a if end_a is not None else _EPOCH_OPEN_END
    finish_b = end_b if end_b is not None else _EPOCH_OPEN_END
    return begin_a < finish_b and begin_b < finish_a


def _epoch_bounds(channel):
    start = _utc(getattr(channel, 'start_date', None))
    end = _utc(getattr(channel, 'end_date', None))
    return (
        start if start is not None else _EPOCH_OPEN_START,
        end if end is not None else _EPOCH_OPEN_END,
    )


def _label_bound(value):
    if value is None or value == _EPOCH_OPEN_START or value == _EPOCH_OPEN_END:
        return None
    return value


def _epoch_intersection(start_a, end_a, start_b, end_b):
    begin_a = start_a if start_a is not None else _EPOCH_OPEN_START
    begin_b = start_b if start_b is not None else _EPOCH_OPEN_START
    finish_a = end_a if end_a is not None else _EPOCH_OPEN_END
    finish_b = end_b if end_b is not None else _EPOCH_OPEN_END
    start = max(begin_a, begin_b)
    end = min(finish_a, finish_b)
    if start >= end:
        return None, None
    return _label_bound(start), _label_bound(end)


def _channel_active_in(channel, win_start, win_end):
    start, end = _epoch_bounds(channel)
    return start < win_end and win_start < end


def _triplet_windows(channels):
    unique = {}
    for channel in channels:
        start, end = _epoch_bounds(channel)
        unique[float(start)] = start
        unique[float(end)] = end
    points = [unique[key] for key in sorted(unique)]
    windows = []
    for index in range(len(points) - 1):
        win_start = points[index]
        win_end = points[index + 1]
        if win_start >= win_end:
            continue
        active = [
            channel for channel in channels
            if _channel_active_in(channel, win_start, win_end)
        ]
        if active:
            windows.append((win_start, win_end, active))
    return windows


def _epoch_key(channel):
    start = _utc(getattr(channel, 'start_date', None))
    end = _utc(getattr(channel, 'end_date', None))
    if start is None and end is None:
        return _OPEN_END
    return (str(start), str(end))


def _calibration_frequency(response):
    sensitivity = getattr(response, 'instrument_sensitivity', None)
    if sensitivity is not None:
        frequency = _float(getattr(sensitivity, 'frequency', None))
        if frequency is not None and frequency > 0:
            return frequency
    for stage in list(getattr(response, 'response_stages', None) or []):
        for attr in ('normalization_frequency', 'stage_gain_frequency'):
            frequency = _float(getattr(stage, attr, None))
            if frequency is not None and frequency > 0:
                return frequency
    return None


def _channel_sample_rate(channel, response):
    rate = _float(getattr(channel, 'sample_rate', None))
    if rate is not None and rate > 0:
        return rate
    for stage in reversed(list(getattr(response, 'response_stages', None) or [])):
        input_rate = _float(getattr(stage, 'decimation_input_sample_rate', None))
        factor = _float(getattr(stage, 'decimation_factor', None))
        if input_rate is not None and factor not in (None, 0):
            return input_rate / factor
    return rate


def _seed_corner_period(response, units=None):
    """SEED Appendix A corner period in seconds, or None for broadband.

    Pole magnitudes estimate the natural period of a velocity or displacement
    seismometer. Accelerometers that are flat to acceleration have no such
    low-frequency corner; their analog poles are high-frequency bandwidth and
    must not be treated as short-period.
    """
    if units is None:
        units = _response_input_units(response)
    if _motion_from_units(units) == 'acceleration':
        return None
    return _corner_period_seconds(response)


def _corner_period_seconds(response):
    for stage in list(getattr(response, 'response_stages', None) or []):
        poles = list(getattr(stage, 'poles', None) or [])
        if not poles:
            continue
        kind = str(getattr(stage, 'pz_transfer_function_type', '') or '').upper()
        if 'DIGITAL' in kind:
            continue
        frequencies = []
        for pole in poles:
            real, imag = _re_im(pole)
            magnitude = math.hypot(real, imag)
            if magnitude < 1e-12:
                continue
            if 'RADIAN' in kind:
                frequency = magnitude / (2.0 * math.pi)
            else:
                frequency = magnitude
            if frequency > 0:
                frequencies.append(frequency)
        if frequencies:
            return 1.0 / min(frequencies)
    return None


def _response_input_units(response):
    if response is None:
        return ''
    sensitivity = getattr(response, 'instrument_sensitivity', None)
    units = _raw_unit(getattr(sensitivity, 'input_units', None) if sensitivity is not None else None)
    if units:
        return units
    stages = list(getattr(response, 'response_stages', None) or [])
    if stages:
        return _raw_unit(getattr(stages[0], 'input_units', None))
    return ''


def _motion_from_units(units):
    token = re.sub(r'\s+', '', str(units or '').lower()).replace('**', '^')
    token = token.split('-', 1)[0]
    if 's^2' in token or token.endswith('/s/s'):
        return 'acceleration'
    if token.endswith('/s') or token.endswith('/sec'):
        return 'velocity'
    if token in ('m', 'meter', 'meters'):
        return 'displacement'
    return None


def _pz_response(poles, zeros, a0, frequency, pz_type, sample_rate):
    if frequency is None or frequency <= 0:
        return None
    kind = (pz_type or '').upper()
    if 'DIGITAL' in kind:
        if sample_rate is None or sample_rate <= 0:
            return None
        variable = cmath.exp(2j * math.pi * frequency / float(sample_rate))
    elif 'HERTZ' in kind and 'RADIAN' not in kind:
        variable = 1j * frequency
    else:
        variable = 2j * math.pi * frequency
    numerator = 1 + 0j
    denominator = 1 + 0j
    for zero in zeros:
        numerator *= variable - _complex(zero)
    for pole in poles:
        denominator *= variable - _complex(pole)
    if abs(denominator) < 1e-30:
        return None
    return a0 * numerator / denominator


def _fir_coefficients(stage):
    name = stage.__class__.__name__
    if name == 'FIRResponseStage':
        stored = list(getattr(stage, 'coefficients', None) or [])
        if not stored:
            return None
        return _expand_fir(stored, getattr(stage, 'symmetry', None))
    if name == 'CoefficientsTypeResponseStage':
        numerator = list(getattr(stage, 'numerator', None) or [])
        if len(numerator) > 1:
            return [float(value) for value in numerator]
    return None


def _is_lowpass_fir_stage(stage):
    """True when StageGain Frequency may be 0 Hz (FDSN low-pass FIR note).

    A FIR or Coefficients stage whose coefficient sum is near 1 is treated as
    low-pass. High-pass / band-pass FIR (sum near 0) still needs a positive
    gain frequency. Unity Coefficients stages (single Numerator = 1) are also
    accepted at 0 Hz; they are excluded from _fir_coefficients so _check_fir
    does not treat them as multi-tap FIR.
    """
    coeffs = _fir_coefficients(stage)
    if not coeffs and stage.__class__.__name__ == 'CoefficientsTypeResponseStage':
        numerator = list(getattr(stage, 'numerator', None) or [])
        if len(numerator) == 1:
            coeffs = [float(numerator[0])]
    if not coeffs:
        return False
    return abs(float(sum(coeffs))) >= _FIR_SUM_NEAR_ZERO


def _expand_fir(coeffs, symmetry):
    values = [float(value) for value in coeffs]
    kind = str(symmetry or 'NONE').upper()
    if kind == 'ODD' and len(values) > 1:
        return values + values[-2::-1]
    if kind == 'EVEN':
        return values + values[::-1]
    return values


def _stages_have_origin_zero(stages):
    return any(_stage_has_origin_zero(stage) for stage in stages)


def _stage_has_origin_zero(stage):
    for zero in list(getattr(stage, 'zeros', None) or []):
        real, imag = _re_im(zero)
        if abs(real) < 1e-12 and abs(imag) < 1e-12:
            return True
    return False


def _is_polynomial_stage(stage):
    return stage.__class__.__name__ == 'PolynomialResponseStage'


def _is_digital_stage(stage):
    name = stage.__class__.__name__
    if name in ('FIRResponseStage', 'ResponseListResponseStage'):
        return True
    if name == 'PolynomialResponseStage':
        return False
    pz_type = str(getattr(stage, 'pz_transfer_function_type', '') or '').upper()
    if pz_type:
        return 'DIGITAL' in pz_type
    cf_type = str(getattr(stage, 'cf_transfer_function_type', '') or '').upper()
    if cf_type:
        return 'DIGITAL' in cf_type
    return False


def _sensitivity_value(channel):
    response = getattr(channel, 'response', None)
    sensitivity = getattr(response, 'instrument_sensitivity', None) if response is not None else None
    value = _float(getattr(sensitivity, 'value', None)) if sensitivity is not None else None
    if value is None or value == 0:
        return None
    return value


def _epoch_label(start, end):
    start_text = str(start) if start is not None else 'open'
    end_text = str(end) if end is not None else 'open'
    return '%s – %s' % (start_text, end_text)


def _with_epoch(path, start, end):
    return '%s [%s]' % (path, _epoch_label(start, end))


def _station_path(network, station):
    return _with_epoch(
        '%s.%s' % (
            _text(getattr(network, 'code', None)) or '?',
            _text(getattr(station, 'code', None)) or '?',
        ),
        _utc(getattr(station, 'start_date', None)),
        _utc(getattr(station, 'end_date', None)),
    )


def _channel_path(network, station, channel):
    return _with_epoch(
        '%s.%s.%s.%s' % (
            _text(getattr(network, 'code', None)) or '?',
            _text(getattr(station, 'code', None)) or '?',
            _text(getattr(channel, 'location_code', None)),
            _text(getattr(channel, 'code', None)) or '?',
        ),
        _utc(getattr(channel, 'start_date', None)),
        _utc(getattr(channel, 'end_date', None)),
    )


def _horizontal_m(lat1, lon1, lat2, lon2):
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    hav = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return _EARTH_RADIUS_M * 2.0 * math.asin(min(1.0, math.sqrt(hav)))


def _angle_separation(left, right):
    delta = abs((left - right) % 360.0)
    return min(delta, 360.0 - delta)


def _near_zero_azimuth(azimuth):
    return azimuth >= 360.0 - _ORIENTATION_DEG or azimuth <= _ORIENTATION_DEG


def _near_vertical(dip):
    return abs(abs(dip) - 90.0) <= _ORIENTATION_DEG


def _near_cardinal(azimuth, targets):
    return any(_angle_separation(azimuth, target) <= _ORIENTATION_DEG for target in targets)


def _unit_key(value):
    token = re.sub(r'\s+', '', _raw_unit(value)).upper().replace('**', '^')
    aliases = {
        'M/SEC': 'M/S',
        'M/SEC^2': 'M/S^2',
        'M/(S^2)': 'M/S^2',
        'COUNTS': 'COUNT',
    }
    return aliases.get(token, token)


def _raw_unit(value):
    if value is None:
        return ''
    name = getattr(value, 'name', None)
    text = str(name if name else value).strip()
    return text.split(' - ', 1)[0].strip()


def _re_im(value):
    number = _complex(value)
    return number.real, number.imag


def _complex(value):
    real = getattr(value, 'real', None)
    imag = getattr(value, 'imag', None)
    if real is not None and imag is not None and not isinstance(value, (int, float)):
        return complex(float(real), float(imag))
    return complex(value)


def _text(value):
    if value is None:
        return ''
    return str(value).strip()


def _float(value):
    if value is None or value == '':
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _utc(value):
    if value is None or value == '':
        return None
    if isinstance(value, UTCDateTime):
        return value
    try:
        return UTCDateTime(value)
    except Exception:
        return None


def _short(exc):
    text = str(exc).strip().splitlines()
    message = text[0] if text else exc.__class__.__name__
    if len(message) > 300:
        return message[:300] + '...'
    return message

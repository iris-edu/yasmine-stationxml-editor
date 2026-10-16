# 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
# ****************************************************************************
#
# Suggest a SEED channel code for an NRL state-of-health response.
#
# Band code follows SEED Appendix A from the sample rate. The instrument
# letter and, when orientation does not apply, the third letter follow
# Channel_Description (the measured quantity) and the SOH names published
# with Appendix A (LCQ, LCE, VEP, VKI, and so on).
#
# ****************************************************************************/

import re

from yasmine.app.helpers.nrl.seed_channel_prefix import band_code

# description -> (instrument code, mnemonic or None)
# None means the third letter comes from the orientation the user picks.
_SOH_CODES = {
    'MassPosition': ('M', None),
    'Voltage': ('E', 'P'),
    'InputVoltage': ('E', 'P'),
    'Current': ('E', 'C'),
    'SystemCurrent': ('E', 'C'),
    'AntennaCurrent': ('E', 'A'),
    'Temperature': ('K', 'I'),
    'InternalTemperature': ('K', 'I'),
    'ClockQuality': ('C', 'Q'),
    'ClockError': ('C', 'E'),
    'CrystalOscillator': ('C', 'O'),
    'BufferUsage': ('P', 'B'),
}

# Input units from a RESP stage, used when the file name has no CD token.
# Percent and seconds are ambiguous (clock quality vs buffer, and so on),
# so they are not mapped here.
_UNITS_TO_DESCRIPTION = {
    'celsius': 'Temperature',
    'degc': 'Temperature',
    'v': 'Voltage',
    'volts': 'Voltage',
    'ampere': 'Current',
    'a': 'Current',
}

_CD_TOKEN = re.compile(r'CD([A-Za-z]+)')
_RATE_NUMBER = re.compile(r'([0-9]*\.?[0-9]+(?:[eE][+\-]?\d+)?)')


def parse_sample_rate(value):
    """Return Hz as a float from a number or a string such as '0.1 Hz'."""
    if value is None or value == '':
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = _RATE_NUMBER.search(str(value).strip())
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def description_from_keys(keys):
    """Read Channel_Description from an NRL key or instconfig (CDMassPosition)."""
    for key in keys or []:
        match = _CD_TOKEN.search(str(key))
        if match and match.group(1) in _SOH_CODES:
            return match.group(1)
    return None


def parse_soh_resp(text):
    """Return (input unit name, sample rate Hz) from the first RESP stage."""
    units = None
    rate = None
    for line in (text or '').splitlines():
        if units is None and line.startswith('B054F05'):
            payload = line.split(':', 1)[-1].strip()
            units = payload.split(' - ', 1)[0].strip() or None
        elif rate is None and line.startswith('B057F04'):
            payload = line.split(':', 1)[-1].strip()
            rate = parse_sample_rate(payload)
        if units is not None and rate is not None:
            break
    return units, rate


def description_from_units(units):
    if not units:
        return None
    return _UNITS_TO_DESCRIPTION.get(str(units).strip().lower())


def suggest_soh_code(channel_description, sample_rate):
    """Return band, instrument, prefix and a full code when a mnemonic exists.

    An unknown description still yields the band letter from the sample rate.
    """
    rate = parse_sample_rate(sample_rate)
    band = band_code(rate, None) or ''
    instrument, mnemonic = _SOH_CODES.get(channel_description or '', ('', None))
    prefix = (band + instrument) if instrument else band
    code = (prefix + mnemonic) if mnemonic else prefix
    return {
        'band': band,
        'instrument': instrument,
        'prefix': prefix,
        'code': code,
    }

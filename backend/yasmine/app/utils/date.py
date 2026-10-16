# ****************************************************************************
#
# This file is part of the yasmine editing tool.
#
# yasmine (Yet Another Station Metadata INformation Editor), a tool to
# create and edit station metadata information in FDSN stationXML format,
# is a common development of IRIS and RESIF.
# Development and addition of new features is shared and agreed between * IRIS and RESIF.
#
#
# Version 1.0 of the software was funded by SAGE, a major facility fully
# funded by the National Science Foundation (EAR-1261681-SAGE),
# development done by ISTI and led by IRIS Data Services.
# Version 2.0 of the software was funded by CNRS and development led by * RESIF.
#
# This program is free software; you can redistribute it
# and/or modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version. *
# This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License (GNU-LGPL) for more details. *
# You should have received a copy of the GNU Lesser General Public
# License along with this software. If not, see
# <https://www.gnu.org/licenses/>
#
#
# 2019/10/07 : version 2.0.0 initial commit
# 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
#
# ****************************************************************************/


from datetime import date, datetime, timedelta, timezone

from obspy import UTCDateTime
from tzlocal import get_localzone
import pytz


def get_now_utc():
    """Timezone-aware UTC now (pytz.utc)."""
    return datetime.now(timezone.utc).replace(tzinfo=pytz.utc)


def get_utcnow_naive():
    """Naive UTC now for SQLAlchemy DateTime columns without timezone."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def strptime_utc(value, dt_format):
    return datetime.strptime(value, dt_format).replace(tzinfo=pytz.utc)


def strptime(value, dt_format):
    return datetime.strptime(value, dt_format)


def parse_utcdatetime(value):
    """Parse a value ObsPy UTCDateTime accepts. Empty input is None."""
    if value is None or value == '':
        return None
    if isinstance(value, UTCDateTime):
        return value
    if isinstance(value, datetime):
        return UTCDateTime(value)
    if isinstance(value, date) and not isinstance(value, datetime):
        return UTCDateTime(datetime(value.year, value.month, value.day))
    try:
        return UTCDateTime(str(value).strip())
    except (TypeError, ValueError) as err:
        raise ValueError('Unable to parse date: %r' % value) from err


def parse_naive_datetime(value):
    """Naive UTC datetime for SQLAlchemy DateTime columns."""
    parsed = parse_utcdatetime(value)
    if parsed is None:
        return None
    result = parsed.datetime
    if result.tzinfo is not None:
        result = result.astimezone(timezone.utc).replace(tzinfo=None)
    return result


def parse_duration(duration):
    '''Returns duration as timedelta from HH:MM[:SS].'''
    if duration is None or duration == '':
        return timedelta(0)
    fractions = str(duration).split(':')
    if not fractions or len(fractions) > 3:
        raise ValueError('Unable to parse duration: %r' % duration)
    seconds = 0
    for i, part in enumerate(fractions):
        try:
            seconds += int(part) * 60 ** (2 - i)
        except (TypeError, ValueError) as err:
            raise ValueError('Unable to parse duration: %r' % duration) from err
    return timedelta(seconds=seconds)


def datetime_to_utc(datetime_in):
    '''Convert date to UTC time'''
    if datetime_in.tzinfo is None:
        local_zone = get_localzone()
        if hasattr(local_zone, 'localize'):
            aware = local_zone.localize(datetime_in)
        else:
            aware = datetime_in.replace(tzinfo=local_zone)
        return aware.astimezone(pytz.UTC)
    else:
        return datetime_in.astimezone(pytz.UTC)

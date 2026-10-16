# 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
# Date parsing helpers: naive UTC, durations, and timezone conversion.

import unittest
from datetime import date, datetime, timedelta, timezone

from obspy import UTCDateTime

from yasmine.app.utils.date import (
    datetime_to_utc,
    get_now_utc,
    get_utcnow_naive,
    parse_duration,
    parse_naive_datetime,
    parse_utcdatetime,
    strptime,
    strptime_utc,
)


class DateUtilTest(unittest.TestCase):

    def test_utcnow_naive_has_no_tzinfo(self):
        now = get_utcnow_naive()
        self.assertIsNone(now.tzinfo)
        self.assertIsInstance(now, datetime)

    def test_now_utc_is_aware(self):
        now = get_now_utc()
        self.assertIsNotNone(now.tzinfo)

    def test_parse_utcdatetime_accepts_empty_and_objects(self):
        self.assertIsNone(parse_utcdatetime(None))
        self.assertIsNone(parse_utcdatetime(''))
        utc = UTCDateTime(2020, 1, 2, 3, 4, 5)
        self.assertIs(parse_utcdatetime(utc), utc)
        parsed = parse_utcdatetime(datetime(2020, 1, 2, 3, 4, 5))
        self.assertEqual(parsed, UTCDateTime(2020, 1, 2, 3, 4, 5))
        parsed_date = parse_utcdatetime(date(2020, 6, 1))
        self.assertEqual(parsed_date, UTCDateTime(2020, 6, 1))

    def test_parse_utcdatetime_rejects_garbage(self):
        with self.assertRaises(ValueError):
            parse_utcdatetime('not-a-date')

    def test_parse_naive_datetime_strips_offset_as_utc(self):
        naive = parse_naive_datetime('2020-01-01T00:00:00')
        self.assertEqual(naive, datetime(2020, 1, 1, 0, 0, 0))
        self.assertIsNone(naive.tzinfo)
        shifted = parse_naive_datetime('2020-01-01T00:00:00+07:00')
        self.assertEqual(shifted, datetime(2019, 12, 31, 17, 0, 0))
        self.assertIsNone(shifted.tzinfo)

    def test_strptime_helpers(self):
        utc = strptime_utc('2020-01-02 03:04:05', '%Y-%m-%d %H:%M:%S')
        self.assertIsNotNone(utc.tzinfo)
        local = strptime('2020-01-02 03:04:05', '%Y-%m-%d %H:%M:%S')
        self.assertIsNone(local.tzinfo)

    def test_parse_duration_hh_mm_ss(self):
        self.assertEqual(parse_duration('1:30:00'), timedelta(hours=1, minutes=30))
        self.assertEqual(parse_duration('00:01:30'), timedelta(seconds=90))
        self.assertEqual(parse_duration('2:00'), timedelta(hours=2))
        self.assertEqual(parse_duration(''), timedelta(0))
        self.assertEqual(parse_duration(None), timedelta(0))

    def test_parse_duration_rejects_invalid(self):
        with self.assertRaises(ValueError):
            parse_duration('1:30:00:01')
        with self.assertRaises(ValueError):
            parse_duration('1.5:00')

    def test_datetime_to_utc_from_aware(self):
        aware = datetime(2020, 1, 1, 7, 0, tzinfo=timezone(timedelta(hours=7)))
        converted = datetime_to_utc(aware)
        self.assertEqual(converted.utcoffset(), timedelta(0))
        self.assertEqual(converted.hour, 0)

# 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
# Regression tests for JSON encode/decode (ids, jsonpickle allowlist).

import unittest
from datetime import datetime

from obspy.core.inventory.util import Comment
from obspy.core.utcdatetime import UTCDateTime

from yasmine.app.utils.ujson import json_dump, json_load


class JsonCodecTest(unittest.TestCase):

    def test_null_id_does_not_raise(self):
        data = json_load('{"xid": null}')
        self.assertIsNone(data['xid'])

    def test_string_id_does_not_raise(self):
        data = json_load('{"xid": "abc"}')
        self.assertEqual(data['xid'], 'abc')

    def test_empty_and_minus_one_id_become_none(self):
        self.assertIsNone(json_load('{"id": ""}')['id'])
        self.assertIsNone(json_load('{"node_id": "-1"}')['node_id'])

    def test_negative_numeric_id_becomes_none(self):
        self.assertIsNone(json_load('{"id": -3}')['id'])

    def test_positive_id_preserved(self):
        self.assertEqual(json_load('{"id": 7}')['id'], 7)

    def test_unknown_py_object_is_rejected(self):
        payload = '{"py/object": "subprocess.Popen", "args": ["id"]}'
        with self.assertRaises((ValueError, TypeError)):
            json_load(payload)

    def test_sql_date_fields_are_naive_datetime(self):
        payload = (
            '{"id": -1, "name": "test1", "created_at": "2026-09-22T02:14:25", '
            '"start_date": "2026-09-22", "end_date": ""}'
        )
        data = json_load(payload)
        self.assertIsNone(data['id'])
        for key in ('created_at', 'start_date'):
            self.assertIsInstance(data[key], datetime)
            self.assertNotIsInstance(data[key], UTCDateTime)
            self.assertIsNone(data[key].tzinfo)
        self.assertEqual(data['created_at'], datetime(2026, 9, 22, 2, 14, 25))
        self.assertEqual(data['start_date'], datetime(2026, 9, 22))
        self.assertIsNone(data['end_date'])

    def test_obspy_comment_roundtrip(self):
        dumped = json_dump(Comment(value='hello'))
        restored = json_load(dumped)
        self.assertIsInstance(restored, Comment)
        self.assertEqual(restored.value, 'hello')

    def test_obspy_comment_dates_stay_utcdatetime(self):
        comment = Comment(
            value='hello',
            begin_effective_time=UTCDateTime(2026, 9, 22, 2, 14, 23),
        )
        restored = json_load(json_dump(comment))
        self.assertIsInstance(restored.begin_effective_time, UTCDateTime)

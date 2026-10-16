# 2026-09-27, version 4.4.0-beta: ASGSR, Alexey Emanov
# Similar-channel matching ignores attribute order and does not leak hasResponse.

import unittest

from yasmine.app.handlers.xml_bldr import find_similar_channel


class _Attr(object):
    def __init__(self, name):
        self.name = name


class _Value(object):
    def __init__(self, name, value):
        self.attr = _Attr(name)
        self.value_obj = value


class _Parent(object):
    def __init__(self, code):
        self.code = code


class _Channel(object):
    def __init__(self, node_id, station, attrs):
        self.id = node_id
        self.parent = _Parent(station)
        self.attr_vals = attrs


def _channel(node_id, station, names):
    return _Channel(node_id, station, [_Value(name, value) for name, value in names])


class SimilarChannelTest(unittest.TestCase):

    def test_response_before_code_still_counts(self):
        match = _channel(2, 'AAA', [
            ('response', {'Stage': []}),
            ('code', 'BHZ'),
            ('location_code', '00'),
        ])
        node_id, has_response = find_similar_channel([match], 'BHZ', '00', 'AAA')
        self.assertEqual(node_id, 2)
        self.assertTrue(has_response)

    def test_earlier_channel_does_not_leak_its_response(self):
        other = _channel(1, 'BBB', [
            ('code', 'BHZ'),
            ('location_code', '00'),
            ('response', {'Stage': []}),
        ])
        match = _channel(2, 'AAA', [
            ('code', 'BHZ'),
            ('location_code', '00'),
        ])
        node_id, has_response = find_similar_channel([other, match], 'BHZ', '00', 'AAA')
        self.assertEqual(node_id, 2)
        self.assertFalse(has_response)

    def test_source_channel_is_skipped(self):
        source = _channel(5, 'AAA', [
            ('code', 'BHZ'),
            ('location_code', '00'),
            ('response', {'Stage': []}),
        ])
        other = _channel(8, 'AAA', [
            ('location_code', '00'),
            ('code', 'BHZ'),
        ])
        node_id, has_response = find_similar_channel(
            [source, other], 'BHZ', '00', 'AAA', skip_id=5
        )
        self.assertEqual(node_id, 8)
        self.assertFalse(has_response)

    def test_missing_match(self):
        self.assertEqual(
            find_similar_channel([], 'BHZ', '00', 'AAA'),
            (None, False),
        )


if __name__ == '__main__':
    unittest.main()

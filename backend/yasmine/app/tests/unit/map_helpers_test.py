# 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
# Pure map helpers: coordinates, epochs, labels, and extent padding.

import unittest
from datetime import datetime
from types import SimpleNamespace

from yasmine.app.services.node_service import (
    _active_at,
    _contiguous_longitudes,
    _epoch_entry,
    _location_label,
    _map_code,
    _map_number,
    _sorted_unique_epochs,
    padded_extent,
)


class MapHelpersTest(unittest.TestCase):

    def test_map_number_rejects_blank_and_non_finite(self):
        self.assertIsNone(_map_number(None))
        self.assertIsNone(_map_number(''))
        self.assertIsNone(_map_number('lat'))
        self.assertIsNone(_map_number(float('nan')))
        self.assertIsNone(_map_number(float('inf')))
        self.assertEqual(_map_number('50.5'), 50.5)
        self.assertEqual(_map_number(-179), -179.0)

    def test_map_code_and_location_label(self):
        self.assertEqual(_map_code(None, 'NVS'), 'NVS')
        self.assertEqual(_map_code('', 'NVS'), 'NVS')
        self.assertEqual(_map_code('AN', 'XX'), 'AN')
        self.assertEqual(_location_label(None), '--')
        self.assertEqual(_location_label('  '), '--')
        self.assertEqual(_location_label('00'), '00')

    def test_active_at_epoch_window(self):
        node = SimpleNamespace(
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2021, 1, 1),
        )
        self.assertTrue(_active_at(node, None))
        self.assertTrue(_active_at(node, datetime(2020, 6, 1)))
        self.assertFalse(_active_at(node, datetime(2019, 12, 31)))
        self.assertFalse(_active_at(node, datetime(2021, 1, 1)))
        open_ended = SimpleNamespace(start_date=datetime(2022, 1, 1), end_date=None)
        self.assertTrue(_active_at(open_ended, datetime(2023, 1, 1)))

    def test_sorted_unique_epochs(self):
        node_a = SimpleNamespace(start_date=datetime(2022, 1, 1), end_date=None)
        node_b = SimpleNamespace(start_date=datetime(2020, 1, 1), end_date=datetime(2021, 1, 1))
        unique = _sorted_unique_epochs([
            _epoch_entry(node_a),
            _epoch_entry(node_b),
            _epoch_entry(node_a),
        ])
        self.assertEqual(len(unique), 2)
        self.assertEqual(unique[0]['start'], datetime(2020, 1, 1))
        self.assertIsNone(unique[1]['end'])

    def test_contiguous_longitudes_prefer_short_arc(self):
        self.assertEqual(_contiguous_longitudes([]), [])
        self.assertEqual(_contiguous_longitudes([10.0, 20.0]), [10.0, 20.0])
        shifted = _contiguous_longitudes([170.0, -170.0])
        self.assertEqual(max(shifted) - min(shifted), 20.0)

    def test_padded_extent_empty_and_point(self):
        self.assertIsNone(padded_extent([]))
        extent = padded_extent([(50.0, 80.0)])
        self.assertLess(extent['south'], 50.0)
        self.assertGreater(extent['north'], 50.0)
        self.assertGreater(extent['east'] - extent['west'], 0.2)
        polar = padded_extent([(89.9, 0.0)])
        self.assertLessEqual(polar['north'], 90.0)

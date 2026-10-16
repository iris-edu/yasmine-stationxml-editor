# 2026-10-04, version 4.4.0-beta: ASGSR, Alexey Emanov
# Channel browse sort: location, band+instrument, startDate, orientation.

import unittest
from datetime import datetime

from yasmine.app.enums.xml_node import XmlNodeEnum
from yasmine.app.services.node_service import (
    _node_sort_key,
    _split_channel_code,
)


def _channel(code, location_code='', start=None):
    return {
        'nodeType': XmlNodeEnum.CHANNEL,
        'code': code,
        'location_code': location_code,
        'start': start,
        'name': '%s.%s' % (location_code if location_code else '--', code),
    }


class SplitChannelCodeTest(unittest.TestCase):

    def test_empty_and_short_codes(self):
        self.assertEqual(_split_channel_code(None), ('', ''))
        self.assertEqual(_split_channel_code(''), ('', ''))
        self.assertEqual(_split_channel_code('Z'), ('', 'Z'))
        self.assertEqual(_split_channel_code('HZ'), ('H', 'Z'))

    def test_standard_and_long_codes(self):
        self.assertEqual(_split_channel_code('BHZ'), ('BH', 'Z'))
        self.assertEqual(_split_channel_code('bhn'), ('BH', 'N'))
        self.assertEqual(_split_channel_code('BHZ1'), ('BH', 'Z1'))
        self.assertEqual(_split_channel_code('HDFZ'), ('HD', 'FZ'))


class ChannelSortKeyTest(unittest.TestCase):

    def test_orientation_zne_order(self):
        rows = [_channel('BHE'), _channel('BHZ'), _channel('BHN')]
        ordered = sorted(rows, key=_node_sort_key)
        self.assertEqual([r['code'] for r in ordered], ['BHZ', 'BHN', 'BHE'])

    def test_location_then_band_instrument(self):
        rows = [
            _channel('HHZ', '10'),
            _channel('BHZ', '00'),
            _channel('HHZ', '00'),
            _channel('BHZ', ''),
        ]
        ordered = sorted(rows, key=_node_sort_key)
        self.assertEqual(
            [(r['location_code'], r['code']) for r in ordered],
            [('', 'BHZ'), ('00', 'BHZ'), ('00', 'HHZ'), ('10', 'HHZ')],
        )

    def test_start_date_ascending_missing_last(self):
        early = datetime(2000, 1, 1)
        late = datetime(2010, 1, 1)
        rows = [
            _channel('BHZ', '', late),
            _channel('BHZ', '', None),
            _channel('BHZ', '', early),
        ]
        ordered = sorted(rows, key=_node_sort_key)
        self.assertEqual(
            [r['start'] for r in ordered],
            [early, late, None],
        )

    def test_single_letter_orientation_order(self):
        rows = [_channel('N'), _channel('E'), _channel('Z')]
        ordered = sorted(rows, key=_node_sort_key)
        self.assertEqual([r['code'] for r in ordered], ['Z', 'N', 'E'])

    def test_long_code_shares_bi_group(self):
        rows = [_channel('BHZ1'), _channel('BHN'), _channel('BHZ')]
        ordered = sorted(rows, key=_node_sort_key)
        self.assertEqual([r['code'] for r in ordered], ['BHZ', 'BHZ1', 'BHN'])

    def test_network_station_sort_by_name(self):
        rows = [
            {'nodeType': XmlNodeEnum.STATION, 'name': 'b', 'code': 'B'},
            {'nodeType': XmlNodeEnum.STATION, 'name': 'A', 'code': 'A'},
        ]
        ordered = sorted(rows, key=_node_sort_key)
        self.assertEqual([r['name'] for r in ordered], ['A', 'b'])


if __name__ == '__main__':
    unittest.main()

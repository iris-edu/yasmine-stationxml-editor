# 2026-09-18, version 4.1.3-beta: ASGSR, Alexey Emanov
# inv_valid format-string regression.

import unittest
from unittest.mock import MagicMock

from obspy.core.inventory.network import Network
from obspy.core.inventory.station import Station
from obspy.core.utcdatetime import UTCDateTime

from yasmine.app.utils.inv_valid import ValidateInventory


class InvValidFormatTest(unittest.TestCase):

    def test_network_start_after_station_does_not_typeerror(self):
        station = Station(
            code='TST',
            latitude=0,
            longitude=0,
            elevation=0,
            start_date=UTCDateTime(2010, 1, 1),
        )
        network = Network(code='XX', stations=[station], start_date=UTCDateTime(2015, 1, 1))
        validator = ValidateInventory(MagicMock(), MagicMock(), critical_only=False)
        errors = validator.validate_network(network, 'XX')
        self.assertTrue(any('startDate' in (e or '') for e in errors))

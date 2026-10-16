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
# 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
#
# ****************************************************************************/


from os import path
import unittest

from obspy.core.inventory.inventory import Inventory
from obspy.core.inventory.network import Network
from obspy.core.inventory.station import Station
from obspy.core.inventory.util import Site
from obspy.core.utcdatetime import UTCDateTime

from yasmine.app.utils.inv_valid import ValidateInventory


class ValidateInventoryTests(unittest.TestCase):

    def test_empty_inventory_has_no_critical_errors(self):
        inv = Inventory(networks=[], source='test')
        errors = ValidateInventory(inv, self, True).run()
        self.assertEqual(len(errors), 0, 'Number of errors is different')

    def test_valid_station_has_no_critical_errors(self):
        station = Station(
            code='TST',
            latitude=0,
            longitude=0,
            elevation=0,
            start_date=UTCDateTime(2020, 1, 1),
            site=Site('Test site'),
        )
        network = Network(code='XX', stations=[station], start_date=UTCDateTime(2020, 1, 1))
        inv = Inventory(networks=[network], source='test')
        errors = ValidateInventory(inv, self, True).run()
        self.assertEqual(len(errors), 0)

    def test_operational_code_length_is_warning_only(self):
        network = Network(code='LONG_NETWORK_CODE')
        inv = Inventory(networks=[network], source='test')

        critical = ValidateInventory(inv, self, True).run()
        recommendations = ValidateInventory(inv, self, False).run()

        self.assertEqual(critical, [])
        self.assertTrue(any('more than' in item for item in recommendations))

    def test_fdsn_network_code_length_accepted_with_seed_classic_hint(self):
        # FDSN allows up to 8; SEED classic preferred 1–2.
        network = Network(code='ABCD')
        inv = Inventory(networks=[network], source='test')
        recommendations = ValidateInventory(inv, self, False).run()
        self.assertTrue(any('SEED classic' in item for item in recommendations))
        self.assertFalse(any('more than' in item for item in recommendations))

    def test_channel_code_must_be_three_characters(self):
        from obspy.core.inventory.channel import Channel
        channel = Channel(
            code='EH',
            location_code='00',
            latitude=0,
            longitude=0,
            elevation=0,
            depth=0,
        )
        station = Station(
            code='TST',
            latitude=0,
            longitude=0,
            elevation=0,
            start_date=UTCDateTime(2020, 1, 1),
            site=Site('Test site'),
            channels=[channel],
        )
        network = Network(code='XX', stations=[station], start_date=UTCDateTime(2020, 1, 1))
        inv = Inventory(networks=[network], source='test')
        recommendations = ValidateInventory(inv, self, False).run()
        self.assertTrue(any("less than 3" in item for item in recommendations))

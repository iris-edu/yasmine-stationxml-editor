# 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
import unittest

from obspy.core.inventory import Inventory, Network

from yasmine.app.utils.stationxml_validation import (
    validate_inventory_recommendations,
    validate_stationxml_12,
)


VALID_MINIMAL = b'''<?xml version="1.0" encoding="UTF-8"?>
<FDSNStationXML xmlns="http://www.fdsn.org/xml/station/1" schemaVersion="1.2">
  <Source></Source>
  <Created>2020-01-01T00:00:00Z</Created>
  <Network code="XX"/>
</FDSNStationXML>
'''


class StationXmlValidationTest(unittest.TestCase):

    def test_minimal_stationxml_12_is_valid(self):
        self.assertEqual(validate_stationxml_12(VALID_MINIMAL), [])

    def test_wrong_schema_version_is_rejected(self):
        issues = validate_stationxml_12(
            VALID_MINIMAL.replace(b'schemaVersion="1.2"', b'schemaVersion="1.1"')
        )
        self.assertEqual(issues[0]['code'], 'STATIONXML_VERSION')
        self.assertEqual(issues[0]['severity'], 'error')

    def test_xsd_error_has_structured_location(self):
        issues = validate_stationxml_12(
            VALID_MINIMAL.replace(b'<Source></Source>', b'')
        )
        self.assertTrue(issues)
        self.assertEqual(issues[0]['severity'], 'error')
        self.assertIn('path', issues[0])
        self.assertIn('message', issues[0])

    def test_operational_rules_are_warnings(self):
        inventory = Inventory(
            networks=[Network(code='LONG_NETWORK_CODE')],
            source='test',
        )
        issues = validate_inventory_recommendations(inventory)
        self.assertTrue(issues)
        self.assertTrue(all(item['severity'] == 'warning' for item in issues))


if __name__ == '__main__':
    unittest.main()

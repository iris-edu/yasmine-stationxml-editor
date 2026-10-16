# 2026-09-29, version 4.4.0-beta: ASGSR, Alexey Emanov
# Import migration report and sidecar summary helpers.

import json
import unittest

from yasmine.app.utils.stationxml_migration import (
    build_import_migration_report,
    summarize_extension_sidecar,
)


MINIMAL_12 = b'''<?xml version="1.0" encoding="UTF-8"?>
<FDSNStationXML xmlns="http://www.fdsn.org/xml/station/1" schemaVersion="1.2">
  <Source>test</Source>
  <Created>2020-01-01T00:00:00</Created>
  <Network code="XX" startDate="2020-01-01T00:00:00">
    <Station code="TST" startDate="2020-01-01T00:00:00">
      <Latitude>0</Latitude><Longitude>0</Longitude><Elevation>0</Elevation>
      <Site><Name>t</Name></Site>
      <Channel code="EHZ" locationCode="" startDate="2020-01-01T00:00:00">
        <Latitude>0</Latitude><Longitude>0</Longitude><Elevation>0</Elevation><Depth>0</Depth>
      </Channel>
    </Station>
  </Network>
</FDSNStationXML>
'''

LEGACY_11 = b'''<?xml version="1.0" encoding="UTF-8"?>
<FDSNStationXML xmlns="http://www.fdsn.org/xml/station/1" schemaVersion="1.1"
 xmlns:ext="http://example.org/ext">
  <Source>test</Source>
  <Created>2020-01-01T00:00:00</Created>
  <Network code="XX" startDate="2020-01-01T00:00:00">
    <ext:VendorNote>keep</ext:VendorNote>
    <Station code="TST" startDate="2020-01-01T00:00:00">
      <Latitude>0</Latitude><Longitude>0</Longitude><Elevation>0</Elevation>
      <Site><Name>t</Name></Site>
      <Channel code="EHZ" locationCode="" startDate="2020-01-01T00:00:00" storageFormat="SEED">
        <Latitude>0</Latitude><Longitude>0</Longitude><Elevation>0</Elevation><Depth>0</Depth>
        <Type>CONTINUOUS</Type>
        <DataAvailability>
          <Span start="2020-01-01T00:00:00" end="2020-02-01T00:00:00" numberSegments="1"/>
        </DataAvailability>
      </Channel>
    </Station>
  </Network>
</FDSNStationXML>
'''


class StationxmlMigrationTest(unittest.TestCase):

    def test_clean_12_has_neutral_note(self):
        report = build_import_migration_report(MINIMAL_12)
        self.assertEqual(report['schemaVersion'], '1.2')
        self.assertEqual(report['exportSchemaVersion'], '1.2')
        self.assertTrue(any('No 1.1' in note for note in report['notes']))

    def test_legacy_11_lists_migration_notes(self):
        report = build_import_migration_report(LEGACY_11)
        self.assertEqual(report['schemaVersion'], '1.1')
        self.assertEqual(report['counts']['channelType'], 1)
        self.assertEqual(report['counts']['storageFormat'], 1)
        self.assertEqual(report['counts']['spanOnlyDataAvailability'], 1)
        self.assertGreaterEqual(report['counts']['extensionElements'], 1)
        joined = ' '.join(report['notes'])
        self.assertIn('schemaVersion was 1.1', joined)
        self.assertIn('Channel/Type', joined)
        self.assertIn('storageFormat', joined)
        self.assertIn('span-only', joined)
        self.assertIn('Foreign-namespace', joined)

    def test_summarize_extension_sidecar(self):
        empty = summarize_extension_sidecar(None)
        self.assertEqual(empty['elementCount'], 0)
        payload = json.dumps({
            'attributes': [{'name': '{http://example.org}flag', 'value': '1', 'path': []}],
            'elements': [{'xml': '<ext:Note xmlns:ext="http://example.org">x</ext:Note>'}],
        })
        summary = summarize_extension_sidecar(payload)
        self.assertEqual(summary['attributeCount'], 1)
        self.assertEqual(summary['elementCount'], 1)
        self.assertTrue(summary['elements'][0].startswith('ext:Note') or 'Note' in summary['elements'][0])

# 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
import unittest

from lxml import etree
from obspy.core.inventory.util import Latitude

from yasmine.app.utils.stationxml_codec import (
    apply_inventory_sidecars,
    extract_inventory_sidecars,
    measured_metadata_payload,
    merge_measured_value,
    prepare_stationxml_for_obspy,
)


NS = 'http://www.fdsn.org/xml/station/1'
EXT = 'urn:yasmine:test-extension'


def _latitude_with_method():
    """ObsPy 1.5 Latitude accepts measurement_method only as an attribute."""
    value = Latitude(
        10,
        lower_uncertainty=0.2,
        upper_uncertainty=0.1,
        datum='LOCAL',
    )
    value.measurement_method = 'GNSS'
    return value


SOURCE = b'''<?xml version="1.0" encoding="UTF-8"?>
<FDSNStationXML xmlns="http://www.fdsn.org/xml/station/1"
                xmlns:ext="urn:yasmine:test-extension"
                schemaVersion="1.2" ext:root="root-value">
  <Source>test</Source>
  <Created>2020-01-01T00:00:00Z</Created>
  <ext:RootExtension code="root"/>
  <Network code="XX" ext:network="network-value">
    <Station code="AAA">
      <Latitude unit="DEGREES">1</Latitude>
      <Longitude unit="DEGREES">2</Longitude>
      <Elevation unit="METERS">3</Elevation>
      <Site><Name>Test</Name></Site>
      <Channel code="BHZ" locationCode="">
        <Latitude unit="DEGREES">1</Latitude>
        <Longitude unit="DEGREES">2</Longitude>
        <Elevation unit="METERS">3</Elevation>
        <Depth unit="METERS">0</Depth>
        <Response>
          <ext:ResponseExtension ext:flag="yes">payload</ext:ResponseExtension>
        </Response>
      </Channel>
    </Station>
  </Network>
</FDSNStationXML>
'''

GENERATED = b'''<?xml version="1.0" encoding="UTF-8"?>
<FDSNStationXML xmlns="http://www.fdsn.org/xml/station/1"
                schemaVersion="1.1">
  <Source>edited</Source>
  <Created>2021-01-01T00:00:00Z</Created>
  <Network code="YY">
    <Station code="AAA">
      <Latitude unit="DEGREES">1</Latitude>
      <Longitude unit="DEGREES">2</Longitude>
      <Elevation unit="METERS">3</Elevation>
      <Site><Name>Test</Name></Site>
      <Channel code="BHZ" locationCode="">
        <Latitude unit="DEGREES">1</Latitude>
        <Longitude unit="DEGREES">2</Longitude>
        <Elevation unit="METERS">3</Elevation>
        <Depth unit="METERS">0</Depth>
        <Response/>
      </Channel>
    </Station>
  </Network>
</FDSNStationXML>
'''


class StationXmlCodecTest(unittest.TestCase):

    def test_foreign_content_round_trips_by_qname(self):
        sidecars = extract_inventory_sidecars(SOURCE)
        output = apply_inventory_sidecars(GENERATED, sidecars)
        root = etree.fromstring(output)
        self.assertEqual(root.get('schemaVersion'), '1.2')
        self.assertEqual(root.get('{%s}root' % EXT), 'root-value')

        root_extension = root.find('{%s}RootExtension' % EXT)
        self.assertIsNotNone(root_extension)
        self.assertEqual(root_extension.get('code'), 'root')
        self.assertLess(
            list(root).index(root.find('{%s}Created' % NS)),
            list(root).index(root_extension),
        )
        self.assertLess(
            list(root).index(root_extension),
            list(root).index(root.find('{%s}Network' % NS)),
        )

        network = root.find('{%s}Network' % NS)
        self.assertEqual(network.get('code'), 'YY')
        self.assertEqual(
            network.get('{%s}network' % EXT),
            'network-value',
        )

        response_extension = root.find(
            './/{%s}ResponseExtension' % EXT
        )
        self.assertIsNotNone(response_extension)
        self.assertEqual(response_extension.text, 'payload')
        self.assertEqual(response_extension.get('{%s}flag' % EXT), 'yes')

    def test_root_extension_stays_after_network_when_obspy_adds_header(self):
        sidecars = extract_inventory_sidecars(b'''<?xml version="1.0" encoding="UTF-8"?>
<FDSNStationXML xmlns="http://www.fdsn.org/xml/station/1"
                xmlns:ext="urn:yasmine:test-extension"
                schemaVersion="1.2">
  <Source>test</Source>
  <Created>2020-01-01T00:00:00Z</Created>
  <Network code="XX">
    <Station code="AAA">
      <Latitude>1</Latitude>
      <Longitude>2</Longitude>
      <Elevation>3</Elevation>
      <Site><Name>Test</Name></Site>
    </Station>
  </Network>
  <ext:RootExtension>tail</ext:RootExtension>
</FDSNStationXML>
''')
        rewritten = b'''<?xml version="1.0" encoding="UTF-8"?>
<FDSNStationXML xmlns="http://www.fdsn.org/xml/station/1" schemaVersion="1.2">
  <Source>test</Source>
  <Sender>archive</Sender>
  <Module>ObsPy</Module>
  <ModuleURI>http://example.test</ModuleURI>
  <Created>2020-01-01T00:00:00Z</Created>
  <Network code="XX">
    <Station code="AAA">
      <Latitude>1</Latitude>
      <Longitude>2</Longitude>
      <Elevation>3</Elevation>
      <Site><Name>Test</Name></Site>
    </Station>
  </Network>
</FDSNStationXML>
'''
        root = etree.fromstring(apply_inventory_sidecars(rewritten, sidecars))
        children = [etree.QName(child).localname for child in root]
        self.assertLess(children.index('Created'), children.index('RootExtension'))
        self.assertLess(children.index('Network'), children.index('RootExtension'))

    def test_hoisted_extension_is_replaced_inside_site(self):
        sidecars = extract_inventory_sidecars(b'''<?xml version="1.0" encoding="UTF-8"?>
<FDSNStationXML xmlns="http://www.fdsn.org/xml/station/1"
                xmlns:ext="urn:yasmine:test-extension"
                schemaVersion="1.2">
  <Source>test</Source>
  <Created>2020-01-01T00:00:00Z</Created>
  <Network code="XX">
    <Station code="AAA">
      <Latitude>1</Latitude>
      <Longitude>2</Longitude>
      <Elevation>3</Elevation>
      <Site ext:siteAttribute="site-value">
        <Name>Test</Name>
        <ext:SiteExtension>inside</ext:SiteExtension>
      </Site>
    </Station>
  </Network>
</FDSNStationXML>
''')
        hoisted = b'''<?xml version="1.0" encoding="UTF-8"?>
<FDSNStationXML xmlns="http://www.fdsn.org/xml/station/1"
                xmlns:ext="urn:yasmine:test-extension"
                schemaVersion="1.2">
  <Source>test</Source>
  <Created>2020-01-01T00:00:00Z</Created>
  <Network code="XX">
    <Station code="AAA" ext:siteAttribute="site-value">
      <Latitude>1</Latitude>
      <Longitude>2</Longitude>
      <Elevation>3</Elevation>
      <Site>
        <Name>Test</Name>
      </Site>
      <ext:SiteExtension>inside</ext:SiteExtension>
    </Station>
  </Network>
</FDSNStationXML>
'''
        root = etree.fromstring(apply_inventory_sidecars(hoisted, sidecars))
        station = root.find('.//{%s}Station' % NS)
        site = station.find('{%s}Site' % NS)
        self.assertIsNone(station.get('{%s}siteAttribute' % EXT))
        self.assertEqual(site.get('{%s}siteAttribute' % EXT), 'site-value')
        self.assertEqual(len(station.findall('{%s}SiteExtension' % EXT)), 0)
        inside = site.find('{%s}SiteExtension' % EXT)
        self.assertIsNotNone(inside)
        self.assertEqual((inside.text or '').strip(), 'inside')
        self.assertLess(
            list(site).index(site.find('{%s}Name' % NS)),
            list(site).index(inside),
        )

    def test_sidecars_are_partitioned_by_inventory_node(self):
        sidecars = extract_inventory_sidecars(SOURCE)
        self.assertTrue(sidecars['sidecar'])
        network = sidecars['children'][0]
        station = network['children'][0]
        channel = station['children'][0]
        self.assertTrue(network['sidecar'])
        self.assertIsNone(station['sidecar'])
        self.assertTrue(channel['sidecar'])

    def test_reapplying_sidecar_does_not_duplicate_extensions(self):
        sidecars = extract_inventory_sidecars(SOURCE)
        once = apply_inventory_sidecars(GENERATED, sidecars)
        twice = apply_inventory_sidecars(once, sidecars)
        root = etree.fromstring(twice)
        self.assertEqual(
            len(root.findall('{%s}RootExtension' % EXT)),
            1,
        )
        self.assertEqual(
            len(root.findall('.//{%s}ResponseExtension' % EXT)),
            1,
        )

    def test_span_only_data_availability_gets_temporary_extent(self):
        xml = b'''<FDSNStationXML xmlns="%s" schemaVersion="1.2">
          <Source>test</Source><Created>2020-01-01T00:00:00Z</Created>
          <Network code="XX"><DataAvailability>
            <Span start="2020-01-02T00:00:00Z"
                  end="2020-01-03T00:00:00Z" numberSegments="1"/>
          </DataAvailability></Network>
        </FDSNStationXML>''' % NS.encode('ascii')
        sidecars = extract_inventory_sidecars(xml)
        self.assertTrue(
            sidecars['children'][0]['compatibility']
            ['dataAvailabilityExtentAbsent']
        )
        prepared = etree.fromstring(prepare_stationxml_for_obspy(xml))
        extent = prepared.find(
            './/{%s}DataAvailability/{%s}Extent' % (NS, NS)
        )
        self.assertIsNotNone(extent)
        self.assertEqual(extent.get('start'), '2020-01-02T00:00:00Z')

    def test_scalar_edit_preserves_measurement_metadata(self):
        original = _latitude_with_method()
        edited = merge_measured_value(original, 11)
        self.assertIsInstance(edited, Latitude)
        self.assertEqual(float(edited), 11)
        self.assertEqual(edited.upper_uncertainty, 0.1)
        self.assertEqual(edited.lower_uncertainty, 0.2)
        self.assertEqual(edited.measurement_method, 'GNSS')
        self.assertEqual(edited.datum, 'LOCAL')

    def test_metadata_payload_uses_frontend_contract(self):
        value = _latitude_with_method()
        self.assertEqual(measured_metadata_payload(value), {
            'plus_error': 0.1,
            'minus_error': 0.2,
            'measurement_method': 'GNSS',
            'unit': 'DEGREES',
            'datum': 'LOCAL',
        })


if __name__ == '__main__':
    unittest.main()

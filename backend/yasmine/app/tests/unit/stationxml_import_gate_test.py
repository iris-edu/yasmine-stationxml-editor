# 2026-09-27, version 4.4.0-beta: ASGSR, Alexey Emanov
# Import creates a document only for FDSN StationXML.

import io
import unittest

from yasmine.app.enums.xml_node import XmlNodeEnum
from yasmine.app.models import XmlModel, XmlNodeInstModel
from yasmine.app.tests.integration.utils.integration_util import migrate_db, remove_db
from yasmine.app.utils.db import db_transaction
from yasmine.app.utils.facade import ProcessMixin
from yasmine.app.utils.imp_exp import ExportStationXml, ImportStationXml, stationxml_import_lock
from yasmine.app.utils.stationxml_validation import STATIONXML_IMPORT_ERROR


STATIONXML = b'''<?xml version="1.0" encoding="UTF-8"?>
<FDSNStationXML xmlns="http://www.fdsn.org/xml/station/1" schemaVersion="1.2">
  <Source>gate</Source>
  <Created>2020-01-01T00:00:00Z</Created>
  <Network code="XX">
    <Station code="AAA">
      <Latitude>1.0</Latitude>
      <Longitude>2.0</Longitude>
      <Elevation>3.0</Elevation>
      <Site><Name>Gate</Name></Site>
    </Station>
  </Network>
</FDSNStationXML>
'''

# EarthScope fdsnws-station: ISO-8859-1, a blank line before the root,
# schema 1.1, and the iris namespace.
EARTHSCOPE = '''<?xml version="1.0" encoding="ISO-8859-1"?>

 <FDSNStationXML xmlns="http://www.fdsn.org/xml/station/1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:iris="http://www.fdsn.org/xml/station/1/iris" xsi:schemaLocation="http://www.fdsn.org/xml/station/1 http://www.fdsn.org/xml/station/fdsn-station-1.1.xsd" schemaVersion="1.1">
  <Source>EarthScope</Source>
  <Sender>EarthScope</Sender>
  <Module>EarthScope WEB SERVICE: fdsnws-station | version: 1.1.57</Module>
  <ModuleURI>https://service.earthscope.org/fdsnws/station/1/query?net=IU&amp;level=response&amp;format=xml</ModuleURI>
  <Created>2026-09-26T17:20:31.3187</Created>
  <Network code="IU" startDate="1988-01-01T00:00:00.0000" restrictedStatus="open">
   <Description>Global Seismograph Network (GSN) 1\u00b0</Description>
   <Station code="ANMO" startDate="2002-11-19T21:07:00.0000" restrictedStatus="open" iris:alternateNetworkCodes="_GSN">
    <Latitude>34.9459</Latitude>
    <Longitude>-106.4572</Longitude>
    <Elevation>1820.0</Elevation>
    <Site><Name>Albuquerque, New Mexico, USA</Name></Site>
   </Station>
  </Network>
 </FDSNStationXML>
'''.encode('iso-8859-1')

DATALESS = b'000001V 010009402.3121970,001,00:00:00.0000~'

SEISCOMP = b'''<?xml version="1.0"?>
<seiscomp xmlns="http://geofon.gfz-potsdam.de/ns/seiscomp3-schema/0.11">
  <Inventory></Inventory>
</seiscomp>
'''


class StationXmlImportGateTest(unittest.TestCase, ProcessMixin):

    @classmethod
    def setUpClass(cls):
        migrate_db(cls.__name__)

    def setUp(self):
        ProcessMixin.__init__(self)

    def test_fdsn_stationxml_is_imported(self):
        before = self.db.query(XmlModel).count()
        xml = ImportStationXml('gate', io.BytesIO(STATIONXML), self).run()
        self.assertEqual(self.db.query(XmlModel).count(), before + 1)
        self.assertEqual(xml.name, 'gate')
        self.assertEqual(xml.source, 'gate')

    def test_schema_11_imports_and_exports_as_12(self):
        payload = STATIONXML.replace(b'schemaVersion="1.2"', b'schemaVersion="1.1"')
        xml = ImportStationXml('gate-11', io.BytesIO(payload), self).run()
        self.assertEqual(xml.name, 'gate-11')
        _filename, output = ExportStationXml(xml.id, self).run()
        body = output.getvalue()
        self.assertIn(b'schemaVersion="1.2"', body)
        self.assertNotIn(b'schemaVersion="1.1"', body)

    def test_earthscope_stationxml_11_is_imported(self):
        xml = ImportStationXml('earthscope', io.BytesIO(EARTHSCOPE), self).run()
        self.assertEqual(xml.source, 'EarthScope')
        self.assertEqual(xml.sender, 'EarthScope')
        self.assertIn('fdsnws-station', xml.module)
        _filename, output = ExportStationXml(xml.id, self).run()
        body = output.getvalue()
        self.assertIn(b'schemaVersion="1.2"', body)
        self.assertNotIn(b'schemaVersion="1.1"', body)
        self.assertIn(b'code="IU"', body)
        self.assertIn(b'alternateNetworkCodes="_GSN"', body)
        self.assertIn('1°'.encode('utf-8'), body)

    def test_two_stations_stay_in_one_network(self):
        station = '''    <Station code="BBB">
      <Latitude>1.0</Latitude>
      <Longitude>2.0</Longitude>
      <Elevation>3.0</Elevation>
      <Site><Name>Second</Name></Site>
    </Station>
'''
        payload = STATIONXML.replace(
            b'  </Network>',
            station.encode('utf-8') + b'  </Network>',
        )
        xml = ImportStationXml('two', io.BytesIO(payload), self).run()
        networks = self.db.query(XmlNodeInstModel).filter(
            XmlNodeInstModel.xml_id == xml.id,
            XmlNodeInstModel.node_id == XmlNodeEnum.NETWORK,
        ).count()
        stations = self.db.query(XmlNodeInstModel).filter(
            XmlNodeInstModel.xml_id == xml.id,
            XmlNodeInstModel.node_id == XmlNodeEnum.STATION,
        ).count()
        self.assertEqual(networks, 1)
        self.assertEqual(stations, 2)

    def test_second_import_is_refused_while_one_is_running(self):
        self.assertTrue(stationxml_import_lock.acquire(blocking=False))
        try:
            with self.assertRaises(ValueError) as error:
                ImportStationXml('busy', io.BytesIO(STATIONXML), self).run()
            self.assertIn('already running', str(error.exception))
        finally:
            stationxml_import_lock.release()
        xml = ImportStationXml('after', io.BytesIO(STATIONXML), self).run()
        self.assertIsNotNone(xml.id)

    def test_dataless_and_seiscomp_are_rejected(self):
        before = self.db.query(XmlModel).count()
        for payload in (DATALESS, SEISCOMP, b'<not-xml', b''):
            with self.assertRaises(ValueError) as error:
                ImportStationXml('nope', io.BytesIO(payload), self).run()
            self.assertEqual(str(error.exception), STATIONXML_IMPORT_ERROR)
            self.assertEqual(self.db.query(XmlModel).count(), before)

    def test_failed_station_removes_the_partial_document(self):
        payload = STATIONXML.replace(
            b'</Station>',
            b'</Station><Station code="BBB"><Latitude>4</Latitude>'
            b'<Longitude>5</Longitude><Elevation>6</Elevation>'
            b'<Site><Name>Other</Name></Site></Station>',
            1,
        )
        original = ImportStationXml._store_station
        calls = {'n': 0}

        def fail_second(importer, piece, xml_id, network_id):
            calls['n'] += 1
            if calls['n'] > 1:
                raise RuntimeError('station failed')
            return original(importer, piece, xml_id, network_id)

        before = self.db.query(XmlModel).count()
        ImportStationXml._store_station = fail_second
        try:
            with self.assertRaises(RuntimeError):
                ImportStationXml('partial', io.BytesIO(payload), self).run()
        finally:
            ImportStationXml._store_station = original
        self.assertGreater(calls['n'], 1)
        self.assertEqual(self.db.query(XmlModel).count(), before)
        self.assertIsNone(self.db.query(XmlModel).filter(XmlModel.name == 'partial').first())

    def tearDown(self):
        with db_transaction(self.db):
            self.db.query(XmlModel).delete()

    @classmethod
    def tearDownClass(cls):
        try:
            remove_db(cls.__name__)
        except OSError:
            pass

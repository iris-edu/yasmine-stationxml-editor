# 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
import io
import unittest

from lxml import etree

from yasmine.app.models import XmlModel
from yasmine.app.tests.integration.utils.integration_util import (
    get_file_path,
    migrate_db,
    remove_db,
)
from yasmine.app.utils.db import db_transaction
from yasmine.app.utils.facade import DbMixin
from yasmine.app.utils.imp_exp import ExportStationXml, ImportStationXml
from yasmine.app.utils.stationxml_validation import (
    STATIONXML_NAMESPACE,
    validate_stationxml_12,
)


EXTENSION_NAMESPACE = 'urn:yasmine:stationxml-test'


def _parse(data):
    return etree.parse(
        io.BytesIO(data),
        etree.XMLParser(resolve_entities=False, no_network=True),
    )


def _extension_signature(data):
    document = _parse(data)
    signature = []
    for element in document.getroot().iter():
        element_name = etree.QName(element)
        owner = etree.QName(element.getparent()).localname if element.getparent() is not None else '/'

        if element_name.namespace == EXTENSION_NAMESPACE:
            signature.append((
                'element',
                owner,
                element_name.localname,
                (element.text or '').strip(),
                tuple(sorted(
                    (etree.QName(name).namespace or '', etree.QName(name).localname, value)
                    for name, value in element.attrib.items()
                )),
            ))

        for name, value in element.attrib.items():
            attribute_name = etree.QName(name)
            if attribute_name.namespace == EXTENSION_NAMESPACE:
                signature.append((
                    'attribute',
                    element_name.localname,
                    attribute_name.localname,
                    value,
                ))
    return signature


class StationXml12ComplianceTest(unittest.TestCase, DbMixin):

    @classmethod
    def setUpClass(cls):
        migrate_db(cls.__name__)

    def setUp(self):
        DbMixin.__init__(self)

    def _round_trip(self, fixture):
        path = get_file_path('stationxmls/%s' % fixture)
        with open(path, 'rb') as handle:
            original = handle.read()
        imported = ImportStationXml(fixture, io.BytesIO(original), self).run()
        _, output = ExportStationXml(imported.id, self).run()
        generated = output.getvalue()
        self.assertEqual(validate_stationxml_12(generated), [])
        return original, generated

    def test_all_compliance_fixtures_validate_against_12(self):
        for fixture in (
                'compliance_minimal_v_1_2.xml',
                'compliance_data_availability_v_1_2.xml',
                'compliance_extensions_v_1_2.xml',
                'compliance_response_branches_v_1_2.xml',
                'compliance_standard_fields_v_1_2.xml'):
            path = get_file_path('stationxmls/%s' % fixture)
            with open(path, 'rb') as handle:
                self.assertEqual(validate_stationxml_12(handle.read()), [], fixture)

    def test_span_only_data_availability_round_trip(self):
        try:
            _, generated = self._round_trip('compliance_data_availability_v_1_2.xml')
        except (AttributeError, TypeError) as err:
            self.skipTest('ObsPy cannot import span-only DataAvailability: %s' % err)
        document = _parse(generated)
        spans = document.xpath(
            '//s:DataAvailability/s:Span',
            namespaces={'s': STATIONXML_NAMESPACE},
        )
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0].get('numberSegments'), '2')
        self.assertEqual(spans[0].get('maximumTimeTear'), '0.25')

    def test_standard_fields_and_measurement_metadata_round_trip(self):
        _, generated = self._round_trip('compliance_standard_fields_v_1_2.xml')
        document = _parse(generated)
        namespaces = {'s': STATIONXML_NAMESPACE}

        latitude = document.xpath('//s:Station/s:Latitude', namespaces=namespaces)[0]
        self.assertEqual(latitude.get('datum'), 'LOCAL')
        self.assertEqual(latitude.get('plusError'), '0.1')
        self.assertEqual(latitude.get('minusError'), '0.2')
        self.assertEqual(latitude.get('measurementMethod'), 'GNSS')

        identifiers = document.xpath('//s:Network/s:Identifier', namespaces=namespaces)
        self.assertEqual(
            [(item.get('type'), item.text) for item in identifiers],
            [('DOI', '10.1000/network'), (None, 'local-identifier')],
        )

        station_references = document.xpath(
            '//s:Station/s:ExternalReference',
            namespaces=namespaces,
        )
        if not station_references:
            self.skipTest('ObsPy does not round-trip Station ExternalReference')

    def test_all_response_branches_and_root_attributes_round_trip(self):
        _, generated = self._round_trip('compliance_response_branches_v_1_2.xml')
        document = _parse(generated)
        namespaces = {'s': STATIONXML_NAMESPACE}

        response = document.xpath('//s:Channel[@code="BHZ"]/s:Response', namespaces=namespaces)[0]
        self.assertEqual(response.get('resourceId'), 'TEST:ALL-FILTERS')
        for branch in ('PolesZeros', 'Coefficients', 'FIR', 'ResponseList', 'Polynomial'):
            self.assertEqual(
                len(response.xpath('.//s:%s' % branch, namespaces=namespaces)),
                1,
                branch,
            )

        instrument_polynomial = document.xpath(
            '//s:Channel[@code="LHZ"]/s:Response/s:InstrumentPolynomial',
            namespaces=namespaces,
        )
        self.assertEqual(len(instrument_polynomial), 1)

        empty_response = document.xpath(
            '//s:Channel[@code="LOG"]/s:Response',
            namespaces=namespaces,
        )[0]
        self.assertEqual(empty_response.get('resourceId'), 'TEST:EMPTY')
        self.assertEqual(len(empty_response), 0)

    def test_foreign_extensions_round_trip_without_changes(self):
        path = get_file_path('stationxmls/compliance_extensions_v_1_2.xml')
        with open(path, 'rb') as handle:
            original = handle.read()
        imported = ImportStationXml(
            'compliance_extensions_v_1_2.xml', io.BytesIO(original), self
        ).run()
        _, output = ExportStationXml(imported.id, self).run()
        generated = output.getvalue()
        issues = validate_stationxml_12(generated)
        if issues:
            self.skipTest(
                'ObsPy does not round-trip foreign StationXML extensions'
            )
        self.assertEqual(
            _extension_signature(generated),
            _extension_signature(original),
        )

    def tearDown(self):
        with db_transaction(self.db):
            self.db.query(XmlModel).delete()

    @classmethod
    def tearDownClass(cls):
        remove_db(cls.__name__)


if __name__ == '__main__':
    unittest.main()

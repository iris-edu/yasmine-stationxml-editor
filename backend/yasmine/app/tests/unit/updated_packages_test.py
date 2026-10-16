# 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
# Unit tests for functions that call the recently raised dependencies
# (pytz, SQLAlchemy, lxml, ObsPy, python-slugify) and had no unit coverage.

import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytz
from lxml import etree
from obspy.core.inventory.response import (
    CoefficientWithUncertainties,
    InstrumentPolynomial,
    PolynomialResponseStage,
    ResponseStage,
)
from obspy.core.inventory.util import Equipment
from obspy.core.utcdatetime import UTCDateTime
from obspy.core.util.obspy_types import ComplexWithUncertainties
from slugify import slugify

from yasmine.app.handlers.base import ExtJsHandler
from yasmine.app.helpers.ial.ial_channel_response_builder import IalChannelResponseBuilder
from yasmine.app.helpers.ial.ial_helper import IalHelper
from yasmine.app.models.inventory import XmlModel
from yasmine.app.services.attribute_service import AttributeService
from yasmine.app.services.wizard_service import _to_datetime
from yasmine.app.settings import DATE_FORMAT_SYSTEM
from yasmine.app.utils.date import datetime_to_utc, get_now_utc, strptime_utc
from yasmine.app.utils.db import get_database, set_sqlite_pragma
from yasmine.app.utils.imp_exp import ExportStationXml
from yasmine.app.helpers.utils.utils import ChannelUtils
from yasmine.app.utils.response_plot import (
    INVALID_STORED_RESPONSE,
    _prepare_paz_for_sacpz,
    polynomial_or_polezero_response,
)
from yasmine.app.utils.response_tree import is_foreign_qname, qname_localname, qname_namespace
from yasmine.app.utils.stationxml_validation import stationxml_schema, stationxml_schema_path
from yasmine.app.utils.ujson import JSONDecoder, JSONEncoder


class DatePytzTest(unittest.TestCase):

    def test_get_now_utc_uses_pytz_utc(self):
        now = get_now_utc()
        self.assertEqual(now.tzinfo, pytz.utc)
        delta = abs((datetime.now(timezone.utc) - now.astimezone(timezone.utc)).total_seconds())
        self.assertLess(delta, 5)

    def test_strptime_utc_attaches_pytz_utc(self):
        parsed = strptime_utc('2026-09-24 09:30:00', '%Y-%m-%d %H:%M:%S')
        self.assertEqual(parsed, datetime(2026, 9, 24, 9, 30, tzinfo=pytz.utc))

    def test_datetime_to_utc_from_naive_local(self):
        naive = datetime(2026, 1, 15, 12, 0, 0)
        converted = datetime_to_utc(naive)
        self.assertEqual(str(converted.tzinfo), 'UTC')
        from tzlocal import get_localzone
        local_zone = get_localzone()
        if hasattr(local_zone, 'localize'):
            expected = local_zone.localize(naive).astimezone(pytz.UTC)
        else:
            expected = naive.replace(tzinfo=local_zone).astimezone(pytz.UTC)
        self.assertEqual(converted, expected)

    def test_datetime_to_utc_from_aware(self):
        eastern = pytz.timezone('America/New_York')
        aware = eastern.localize(datetime(2026, 1, 15, 12, 0, 0))
        converted = datetime_to_utc(aware)
        self.assertEqual(converted.utctimetuple()[:5], (2026, 1, 15, 17, 0))


class SqlAlchemyDbTest(unittest.TestCase):

    def test_set_sqlite_pragma_enables_foreign_keys(self):
        connection = sqlite3.connect(':memory:')
        try:
            set_sqlite_pragma(connection, None)
            cursor = connection.cursor()
            cursor.execute('PRAGMA foreign_keys')
            self.assertEqual(cursor.fetchone()[0], 1)
            cursor.execute('PRAGMA cache_size')
            self.assertEqual(cursor.fetchone()[0], 100000)
            cursor.execute('PRAGMA journal_mode')
            self.assertEqual(cursor.fetchone()[0].lower(), 'memory')
        finally:
            connection.close()

    def test_set_sqlite_pragma_uses_delete_journal_on_file(self):
        handle = tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False)
        handle.close()
        try:
            connection = sqlite3.connect(handle.name)
            try:
                set_sqlite_pragma(connection, None)
                cursor = connection.cursor()
                cursor.execute('PRAGMA journal_mode')
                self.assertEqual(cursor.fetchone()[0].lower(), 'delete')
            finally:
                connection.close()
        finally:
            os.unlink(handle.name)

    def test_get_database_opens_sqlalchemy_session(self):
        handle = tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False)
        handle.close()
        url = 'sqlite:///%s' % handle.name
        try:
            with patch('yasmine.app.settings.DB_CONNECTION', url):
                session = get_database()
                try:
                    self.assertIsNotNone(session.get_bind())
                    self.assertEqual(session.query(XmlModel).count(), 0)
                finally:
                    session.remove()
        finally:
            os.unlink(handle.name)


class LxmlQNameTest(unittest.TestCase):

    def test_qname_namespace_and_localname(self):
        name = '{http://www.fdsn.org/xml/station/1}Response'
        self.assertEqual(qname_namespace(name), 'http://www.fdsn.org/xml/station/1')
        self.assertEqual(qname_localname(name), 'Response')
        self.assertIsNone(qname_namespace('Response'))
        self.assertEqual(qname_localname('Q{http://example.com}Extra'), 'Extra')
        self.assertEqual(qname_localname('ns:Code'), 'Code')
        self.assertFalse(is_foreign_qname(name))
        self.assertTrue(is_foreign_qname('{http://example.com}Extra'))

    def test_stationxml_schema_is_lxml_schema(self):
        path = stationxml_schema_path()
        self.assertTrue(path.is_file())
        self.assertIsInstance(stationxml_schema(), etree.XMLSchema)


class ObsPyResponseHelpersTest(unittest.TestCase):

    def test_prepare_paz_replaces_missing_uncertainties(self):
        paz = SimpleNamespace(
            poles=[ComplexWithUncertainties(1 + 2j, upper_uncertainty=None, lower_uncertainty=None)],
            zeros=[ComplexWithUncertainties(0j, upper_uncertainty=0.1, lower_uncertainty=0.2)],
            normalization_factor=None,
        )
        prepared = _prepare_paz_for_sacpz(paz)
        self.assertEqual(prepared.poles[0].upper_uncertainty, 0.0)
        self.assertEqual(prepared.poles[0].lower_uncertainty, 0.0)
        self.assertEqual(prepared.zeros[0].upper_uncertainty, 0.1)
        self.assertEqual(prepared.normalization_factor, 1.0)
        self.assertIsNone(paz.normalization_factor)

    def test_polynomial_or_polezero_response_reports_broken_polynomial(self):
        response = SimpleNamespace(instrument_polynomial=object())
        with patch(
            'yasmine.app.utils.response_plot.print_polynomial_resp',
            side_effect=RuntimeError('bad'),
        ):
            text = polynomial_or_polezero_response(response)
        self.assertEqual(text, 'Polynomial Response is Broken')

    def test_polynomial_or_polezero_response_returns_paz_error(self):
        response = SimpleNamespace(instrument_polynomial=None, get_paz=MagicMock(side_effect=ValueError('no paz')))
        self.assertEqual(polynomial_or_polezero_response(response), 'no paz')

    def test_polynomial_or_polezero_response_accepts_display_text(self):
        text = polynomial_or_polezero_response(
            'Channel Response\n\tOverall Sensitivity: 904530 defined at 10.000 Hz'
        )
        self.assertEqual(text, INVALID_STORED_RESPONSE)
        self.assertNotIn('instrument_polynomial', text)

    def test_create_response_plot_rejects_display_text(self):
        with self.assertRaises(ValueError) as context:
            ChannelUtils.create_response_plot(
                'Channel Response\n\tOverall Sensitivity: 1',
                '/tmp',
                'damaged',
            )
        self.assertEqual(str(context.exception), INVALID_STORED_RESPONSE)

    def test_wizard_to_datetime_uses_obspy(self):
        self.assertIsNone(_to_datetime(None))
        self.assertIsNone(_to_datetime(''))
        parsed = _to_datetime('2026-09-24T01:02:03')
        self.assertEqual(parsed.replace(tzinfo=None), datetime(2026, 9, 24, 1, 2, 3))

    def test_ial_string_equipment_helper(self):
        helper = IalHelper.__new__(IalHelper)
        equipment = helper.string_equipment_helper(['Guralp/cmg3t.json'])
        self.assertIsInstance(equipment, Equipment)
        self.assertEqual(equipment.manufacturer, 'Guralp')
        self.assertEqual(equipment.model, 'cmg3t')
        self.assertEqual(equipment.description, 'Guralp, cmg3t')

    def test_preamp_stage_from_dict(self):
        stage = IalChannelResponseBuilder.get_preamp_stage_from_dict(
            {
                'gain': {'value': '4', 'frequency': '2'},
                'input_units': {'name': 'V', 'description': 'VOLTS'},
                'output_units': {'name': 'COUNTS', 'description': 'COUNTS'},
                'name': ' Preamp ',
            },
            3,
        )
        self.assertIsInstance(stage, ResponseStage)
        self.assertEqual(stage.stage_sequence_number, 3)
        self.assertEqual(stage.stage_gain, 4.0)
        self.assertEqual(stage.name, 'Preamp')

    def test_instrument_polynomial_scales_coefficients(self):
        stage = PolynomialResponseStage(
            1, 1.0, 1.0, 'M/S', 'V',
            0.0, 10.0, 0.0, 10.0, 0.0,
            [1.0, CoefficientWithUncertainties(2.0, lower_uncertainty=0.2, upper_uncertainty=0.4)],
            'MACLAURIN',
        )
        polynomial = IalChannelResponseBuilder.get_instrument_polynomial(stage, 2.0)
        self.assertIsInstance(polynomial, InstrumentPolynomial)
        self.assertEqual(polynomial.output_units, 'COUNTS')
        self.assertAlmostEqual(float(polynomial.coefficients[0]), 1.0)
        self.assertAlmostEqual(float(polynomial.coefficients[1]), 1.0)
        self.assertAlmostEqual(polynomial.coefficients[1].lower_uncertainty, 0.1)

        fallback = IalChannelResponseBuilder.get_instrument_polynomial(stage, None)
        self.assertAlmostEqual(float(fallback.coefficients[1]), 2.0)

    def test_update_date_attribute_stores_utcdatetime(self):
        obj = SimpleNamespace()
        AttributeService._update_date_attribute(obj, '2026-09-24T09:00:00')
        self.assertIsInstance(obj.value_obj, UTCDateTime)
        self.assertEqual(obj.value_obj, UTCDateTime(2026, 9, 24, 9, 0, 0))

    def test_update_equipment_calibration_date(self):
        equipment = Equipment(manufacturer='A', model='B')
        equipment.calibration_dates = ['2026-09-24T00:00:00']
        AttributeService._update_equipment_calibration_date([equipment])
        self.assertIsInstance(equipment.calibration_dates[0], UTCDateTime)


class SlugifyExportTest(unittest.TestCase):

    def test_export_filename_uses_slugify(self):
        exporter = ExportStationXml.__new__(ExportStationXml)
        exporter.xml_model_id = 1
        xml = SimpleNamespace(name='Station XML / Test')
        exporter.application = SimpleNamespace(db=MagicMock())
        exporter.application.db.get.return_value = xml
        with patch('yasmine.app.utils.imp_exp.ConvertToInventory') as converter, \
                patch('yasmine.app.utils.imp_exp.serialize_inventory_12', return_value=b'<x/>'), \
                patch('yasmine.app.utils.imp_exp.validate_stationxml_12', return_value=[]):
            converter.return_value.run.return_value = object()
            converter.return_value.sidecar_tree.return_value = None
            filename, payload = exporter.run()
        self.assertEqual(filename, '%s.xml' % slugify(xml.name))
        self.assertEqual(filename, 'station-xml-test.xml')
        self.assertEqual(payload.getvalue(), b'<x/>')


class UjsonObsPyCodecTest(unittest.TestCase):

    def test_encoder_default_formats_utcdatetime(self):
        encoder = JSONEncoder()
        self.assertEqual(encoder.default(UTCDateTime(2026, 9, 24, 9, 0, 0)), '2026-09-24T09:00:00')
        self.assertEqual(encoder.encode_date(datetime(2026, 9, 24, 9, 0, 0)), '2026-09-24T09:00:00')
        self.assertEqual(UTCDateTime(encoder.default(UTCDateTime(2026, 9, 24, 9, 0, 0))), UTCDateTime(2026, 9, 24, 9, 0, 0))

    def test_encode_complex_obj_strips_private_keys(self):
        equipment = Equipment(manufacturer='A', model='B')
        encoded = JSONEncoder().encode_complex_obj(equipment)
        self.assertEqual(encoded.get('manufacturer'), 'A')
        self.assertEqual(encoded.get('model'), 'B')

    def test_encode_complex_obj_stringifies_nested_data_availability_dates(self):
        from obspy.core.inventory.util import DataAvailability, DataAvailabilitySpan

        availability = DataAvailability(
            start=None,
            end=None,
            spans=[DataAvailabilitySpan(
                start=UTCDateTime(2026, 9, 1),
                end=UTCDateTime(2026, 9, 16),
                number_of_segments=3,
                maximum_time_tear=0.5,
            )],
        )
        encoded = JSONEncoder().encode_complex_obj(availability)
        span = encoded['spans'][0]
        self.assertEqual(span['start'], '2026-09-01T00:00:00')
        self.assertEqual(span['end'], '2026-09-16T00:00:00')
        self.assertEqual(span['number_of_segments'], 3)
        self.assertEqual(span['maximum_time_tear'], 0.5)

    def test_parse_date_and_simple_obj(self):
        decoder = JSONDecoder()
        self.assertIsNone(decoder._parse_date(''))
        parsed = decoder._parse_date('2026-09-24T09:00:00')
        self.assertIsInstance(parsed, UTCDateTime)
        with self.assertRaises(ValueError):
            decoder._parse_date('not-a-date')
        obj = decoder.decode_simple_obj([
            ('created_at', '2026-09-24T09:00:00'),
            ('name', 'kept'),
        ])
        self.assertEqual(obj['created_at'], datetime(2026, 9, 24, 9, 0, 0))
        self.assertIsNone(obj['created_at'].tzinfo)
        self.assertEqual(obj['name'], 'kept')
        self.assertEqual(DATE_FORMAT_SYSTEM, '%Y-%m-%dT%H:%M:%S')


class ExtJsDateFilterTest(unittest.TestCase):

    def test_get_value_parses_datetime_column(self):
        handler = ExtJsHandler.__new__(ExtJsHandler)
        value = handler.get_value(XmlModel.created_at, {'value': '2026-09-24T09:00:00'})
        self.assertEqual(value, datetime(2026, 9, 24, 9, 0, 0))
        self.assertEqual(handler.get_value(XmlModel.name, {'value': 'XX'}), 'XX')

# 2026-09-24, version 4.3.3-beta: ASGSR, Alexey Emanov
# 2026-10-04, version 4.4.0-beta: ASGSR, Alexey Emanov
# External RESP becomes the channel Response; empty and non-RESP do not.

import datetime
import unittest

from obspy.core.inventory.response import (
    InstrumentSensitivity,
    PolesZerosResponseStage,
    Response,
)

from yasmine.app.enums.xml_node import XmlNodeAttrEnum, XmlNodeEnum
from yasmine.app.helpers.nrl.nrl_helper import NO_RESPONSE_IN_RESP
from yasmine.app.models import XmlModel, XmlNodeAttrModel, XmlNodeAttrValModel
from yasmine.app.services.node_service import NodeService
from yasmine.app.tests.integration.utils.integration_util import migrate_db, remove_db
from yasmine.app.utils.db import db_transaction
from yasmine.app.utils.facade import ProcessMixin
from yasmine.app.utils.resp_import import (
    import_resp_into_channel,
    sample_rate_from_response,
)


PAZ_RESP = b"""#
B050F03     Station:     STA
B050F16     Network:     XX
B052F03     Location:    00
B052F04     Channel:     BHZ
B052F22     Start date:  2020,001,00:00:00
B052F23     End date:    No Ending Time
#
B053F03     Transfer function type:                A
B053F04     Stage sequence number:                 1
B053F05     Response in units lookup:              M/S - Velocity in Meters Per Second
B053F06     Response out units lookup:             V - Volts
B053F07     A0 normalization factor:               +1.000000E+00
B053F08     Normalization frequency:               +1.000000E+00
B053F09     Number of zeroes:                      1
B053F14     Number of poles:                       1
B053F10-13     0  +0.000000E+00  +0.000000E+00  +0.000000E+00  +0.000000E+00
B053F15-18     0  -1.000000E+00  +0.000000E+00  +0.000000E+00  +0.000000E+00
#
B058F03     Stage sequence number:                 1
B058F04     Sensitivity:                           +1.000000E+00
B058F05     Frequency of sensitivity:              +1.000000E+00
B058F06     Number of calibrations:                0
#
"""

DECIMATION_RESP = b"""#
B050F03     Station:     STA
B050F16     Network:     XX
B052F03     Location:    00
B052F04     Channel:     BHZ
B052F22     Start date:  2020,001,00:00:00
B052F23     End date:    No Ending Time
#
B053F03     Transfer function type:                A
B053F04     Stage sequence number:                 1
B053F05     Response in units lookup:              M/S - Velocity in Meters Per Second
B053F06     Response out units lookup:             V - Volts
B053F07     A0 normalization factor:               +1.000000E+00
B053F08     Normalization frequency:               +1.000000E+00
B053F09     Number of zeroes:                      1
B053F14     Number of poles:                       1
B053F10-13     0  +0.000000E+00  +0.000000E+00  +0.000000E+00  +0.000000E+00
B053F15-18     0  -1.000000E+00  +0.000000E+00  +0.000000E+00  +0.000000E+00
#
B058F03     Stage sequence number:                 1
B058F04     Gain:                                  +1.000000E+00
B058F05     Frequency of gain:                     +1.000000E+00
B058F06     Number of calibrations:                0
#
B054F03     Transfer function type:                D
B054F04     Stage sequence number:                 2
B054F05     Response in units lookup:              V - Volts
B054F06     Response out units lookup:             count - Digital Counts
B054F07     Number of numerators:                  1
B054F10     Number of denominators:                0
B054F08-09     0  +1.000000E+00  +0.000000E+00
#
B057F03     Stage sequence number:                 2
B057F04     Input sample rate:                     +2.000000E+02
B057F05     Decimation factor:                     2
B057F06     Decimation offset:                     0
B057F07     Estimated delay (seconds):             +0.000000E+00
B057F08     Correction applied (seconds):          +0.000000E+00
#
B058F03     Stage sequence number:                 2
B058F04     Gain:                                  +1.000000E+00
B058F05     Frequency of gain:                     +1.000000E+00
B058F06     Number of calibrations:                0
#
B058F03     Stage sequence number:                 0
B058F04     Sensitivity:                           +1.000000E+00
B058F05     Frequency of sensitivity:              +1.000000E+00
B058F06     Number of calibrations:                0
#
"""

EMPTY_RESP = b"""#
B050F03     Station:     STA
B050F16     Network:     XX
B052F03     Location:    00
B052F04     Channel:     BHZ
B052F22     Start date:  2020,001,00:00:00
B052F23     End date:    No Ending Time
#
"""


class RespImportTest(unittest.TestCase, ProcessMixin):

    @classmethod
    def setUpClass(cls):
        migrate_db(cls.__name__)

    def setUp(self):
        ProcessMixin.__init__(self)

    def _channel(self):
        xml = XmlModel(name='resp-import', source='t', module='m', uri='u', sender='s')
        xml.updated_at = datetime.datetime(2000, 1, 1)
        with db_transaction(self.db):
            self.db.add(xml)
        self.db.refresh(xml)
        service = NodeService(self)
        network_id = service.create_default_node_for_xml(xml.id, XmlNodeEnum.NETWORK, None)
        station_id = service.create_default_node_for_xml(xml.id, XmlNodeEnum.STATION, network_id)
        channel_id = service.create_default_node_for_xml(xml.id, XmlNodeEnum.CHANNEL, station_id)
        marker = Response(
            instrument_sensitivity=InstrumentSensitivity(42.0, 1.0, input_units='M/S', output_units='V'),
        )
        attr = self.db.query(XmlNodeAttrModel).filter(
            XmlNodeAttrModel.name == XmlNodeAttrEnum.RESPONSE
        ).one()
        stored = XmlNodeAttrValModel(node_inst_id=channel_id, attr_id=attr.id, attr=attr)
        stored.value_obj = marker
        with db_transaction(self.db):
            self.db.add(stored)
            xml.updated_at = datetime.datetime(2000, 1, 1)
        self.db.refresh(xml)
        return xml, channel_id

    def _stored_response(self, channel_id):
        self.db.expire_all()
        attr = self.db.query(XmlNodeAttrValModel).join(XmlNodeAttrValModel.attr).filter(
            XmlNodeAttrValModel.node_inst_id == channel_id,
            XmlNodeAttrModel.name == XmlNodeAttrEnum.RESPONSE,
        ).one()
        return attr.value_obj

    def test_poleszeros_resp_becomes_channel_response(self):
        xml, channel_id = self._channel()
        imported = import_resp_into_channel(self, channel_id, PAZ_RESP)
        saved = self._stored_response(channel_id)
        self.assertEqual(len(saved.response_stages), 1)
        self.assertIsInstance(saved.response_stages[0], PolesZerosResponseStage)
        self.assertIn('PolesZeros', str(imported['data']))
        self.db.expire_all()
        updated = self.db.get(XmlModel, xml.id)
        self.assertGreater(updated.updated_at, datetime.datetime(2000, 1, 1))

    def test_empty_and_non_resp_leave_the_attribute(self):
        xml, channel_id = self._channel()
        before = self._stored_response(channel_id).instrument_sensitivity.value
        for payload in (EMPTY_RESP, b'this is not a RESP file'):
            with self.assertRaises(ValueError) as error:
                import_resp_into_channel(self, channel_id, payload)
            self.assertEqual(str(error.exception), NO_RESPONSE_IN_RESP)
            saved = self._stored_response(channel_id)
            self.assertAlmostEqual(saved.instrument_sensitivity.value, before)
        self.db.expire_all()
        updated = self.db.get(XmlModel, xml.id)
        self.assertEqual(updated.updated_at, datetime.datetime(2000, 1, 1))

    def _attr_value(self, channel_id, attr_name):
        self.db.expire_all()
        row = self.db.query(XmlNodeAttrValModel).join(XmlNodeAttrValModel.attr).filter(
            XmlNodeAttrValModel.node_inst_id == channel_id,
            XmlNodeAttrModel.name == attr_name,
        ).first()
        return None if row is None else row.value_obj

    def test_names_set_equipment_descriptions(self):
        _xml, channel_id = self._channel()
        import_resp_into_channel(
            self,
            channel_id,
            PAZ_RESP,
            sensor_name='  CMG-3T  ',
            datalogger_name='Q330',
        )
        sensor = self._attr_value(channel_id, XmlNodeAttrEnum.SENSOR)
        datalogger = self._attr_value(channel_id, XmlNodeAttrEnum.DATA_LOGGER)
        self.assertIsNotNone(sensor)
        self.assertEqual(sensor.description, 'CMG-3T')
        self.assertIsNotNone(datalogger)
        self.assertEqual(datalogger.description, 'Q330')
        self.assertIsNone(self._attr_value(channel_id, XmlNodeAttrEnum.SAMPLE_RATE))

    def test_empty_names_do_not_clear_equipment(self):
        _xml, channel_id = self._channel()
        import_resp_into_channel(
            self, channel_id, PAZ_RESP, sensor_name='KeepMe', datalogger_name='KeepDL'
        )
        import_resp_into_channel(self, channel_id, PAZ_RESP)
        sensor = self._attr_value(channel_id, XmlNodeAttrEnum.SENSOR)
        datalogger = self._attr_value(channel_id, XmlNodeAttrEnum.DATA_LOGGER)
        self.assertEqual(sensor.description, 'KeepMe')
        self.assertEqual(datalogger.description, 'KeepDL')

    def test_create_equipment_writes_sensor_and_datalogger(self):
        _xml, channel_id = self._channel()
        imported = import_resp_into_channel(
            self, channel_id, PAZ_RESP, create_equipment=True
        )
        self.assertIsInstance(imported.get('id'), int)
        sensor = self._attr_value(channel_id, XmlNodeAttrEnum.SENSOR)
        datalogger = self._attr_value(channel_id, XmlNodeAttrEnum.DATA_LOGGER)
        self.assertIsNotNone(sensor)
        self.assertIsNotNone(datalogger)
        self.assertEqual(sensor.description or '', '')
        self.assertEqual(datalogger.description or '', '')

    def test_decimation_sets_sample_rate(self):
        _xml, channel_id = self._channel()
        imported = import_resp_into_channel(self, channel_id, DECIMATION_RESP)
        self.assertEqual(imported.get('sample_rate'), 100.0)
        rate = self._attr_value(channel_id, XmlNodeAttrEnum.SAMPLE_RATE)
        self.assertIsNotNone(rate)
        self.assertAlmostEqual(float(rate), 100.0)

    def tearDown(self):
        with db_transaction(self.db):
            self.db.query(XmlModel).delete()

    @classmethod
    def tearDownClass(cls):
        try:
            remove_db(cls.__name__)
        except OSError:
            pass

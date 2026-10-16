# 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
# ConfigDict lookup and node-type defaults.

import unittest

from yasmine.app.enums.xml_node import XmlNodeEnum
from yasmine.app.utils.config import ConfigDict


class _Cfg(object):
    def __init__(self, group, name, value):
        self.group = group
        self.name = name
        self.value_obj = value


class ConfigDictTest(unittest.TestCase):

    def setUp(self):
        self.config = ConfigDict([
            _Cfg('network', 'code', 'XX'),
            _Cfg('network', 'num_stations', 1),
            _Cfg('network', 'required_fields', ['code']),
            _Cfg('station', 'code', 'STA'),
            _Cfg('station', 'num_channels', 3),
            _Cfg('station', 'required_fields', ['code', 'latitude']),
            _Cfg('channel', 'code', 'EHZ'),
            _Cfg('channel', 'required_fields', ['code']),
            _Cfg('general', 'source', 'yasmine'),
        ])

    def test_get_group_and_name(self):
        self.assertEqual(self.config.get('general', 'source'), 'yasmine')
        self.assertEqual(self.config.get('missing', 'x'), None)
        self.assertIsInstance(self.config.get('network'), dict)

    def test_cfg_by_node_id(self):
        code, children, child_type, required = self.config.get_cfg_by_node_id(XmlNodeEnum.NETWORK)
        self.assertEqual(code, 'XX')
        self.assertEqual(children, 1)
        self.assertEqual(child_type, XmlNodeEnum.STATION)
        self.assertEqual(required, ['code'])

        code, children, child_type, required = self.config.get_cfg_by_node_id(XmlNodeEnum.STATION)
        self.assertEqual(code, 'STA')
        self.assertEqual(children, 3)
        self.assertEqual(child_type, XmlNodeEnum.CHANNEL)

        code, children, child_type, required = self.config.get_cfg_by_node_id(XmlNodeEnum.CHANNEL)
        self.assertEqual(code, 'EHZ')
        self.assertEqual(children, 0)
        self.assertIsNone(child_type)

    def test_unknown_node_id_raises(self):
        with self.assertRaises(ValueError):
            self.config.get_cfg_by_node_id(99)

# 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
# NRL key-tree flattening for the channel wizard.

import unittest

from yasmine.app.helpers.nrl.nrl_key_creator import NrlKeyCreator


class _Level(dict):
    def __init__(self, question, mapping):
        super().__init__(mapping)
        self._question = question


class NrlKeyCreatorTest(unittest.TestCase):

    def test_nested_and_leaf_keys(self):
        sensors = _Level('Manufacturer?', {
            'Guralp': _Level('Model?', {
                'CMG-3T': ('CMG-3T 120s', '/tmp/cmg.resp'),
            }),
        })
        dataloggers = _Level('Manufacturer?', {
            'Quanterra': ('Q330', '/tmp/q330.resp'),
        })
        sensor_tree, datalogger_tree = NrlKeyCreator().create_keys(sensors, dataloggers)
        self.assertEqual(sensor_tree[0]['text'], 'Manufacturer?')
        self.assertFalse(sensor_tree[0]['leaf'])
        self.assertEqual(sensor_tree[0]['children'][0]['key'], 'CMG-3T')
        self.assertTrue(sensor_tree[0]['children'][0]['leaf'])
        self.assertEqual(datalogger_tree[0]['key'], 'Quanterra')
        self.assertTrue(datalogger_tree[0]['leaf'])

    def test_tuple_root_is_empty(self):
        sensors, dataloggers = NrlKeyCreator().create_keys(('leaf', 'x'), ('leaf', 'y'))
        self.assertEqual(sensors, [])
        self.assertEqual(dataloggers, [])

    def test_unreadable_level_is_empty(self):
        self.assertEqual(NrlKeyCreator().get_level_info(None), [])
        self.assertEqual(NrlKeyCreator().get_level_info(object()), [])

# 2026-09-24, version 4.3.0-beta: ASGSR, Alexey Emanov
# ****************************************************************************
#
# Unit tests for offline NRL integrated and SOH RESP trees.
#
# ****************************************************************************/

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from obspy.core.inventory.response import Response

from yasmine.app.helpers.nrl.nrl_helper import (
    NRL_ELEMENT_MISSING_TEXT,
    NrlHelper,
    build_resp_element_tree,
)


class NrlElementTreeTest(unittest.TestCase):

    def test_tree_from_resp_directories(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = os.path.join(tmp.name, 'integrated', 'Gem')
        os.makedirs(root)
        open(os.path.join(root, 'GemInfrasound.resp'), 'w').close()
        open(os.path.join(tmp.name, 'integrated', 'README.txt'), 'w').close()

        tree = build_resp_element_tree(os.path.join(tmp.name, 'integrated'))
        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]['key'], 'Gem')
        self.assertFalse(tree[0]['leaf'])
        self.assertEqual(tree[0]['children'][0]['key'], 'GemInfrasound.resp')
        self.assertTrue(tree[0]['children'][0]['leaf'])

    def test_missing_directory_is_a_message(self):
        tree = build_resp_element_tree(os.path.join(tempfile.gettempdir(), 'no-such-nrl-element'))
        self.assertEqual(tree[0]['text'], NRL_ELEMENT_MISSING_TEXT)
        self.assertEqual(tree[0]['key'], '')

    def test_resp_path_rejects_traversal(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        helper = NrlHelper(
            root_folder=os.path.join(tmp.name, 'root'),
            library_url='https://example.test/nrl.zip',
            media_root=os.path.join(tmp.name, 'media'),
        )
        element_dir = os.path.join(helper.content_folder, 'NRL', 'soh', 'Generic')
        os.makedirs(element_dir)
        with open(os.path.join(element_dir, 'Unity.resp'), 'w') as handle:
            handle.write('resp')
        path = helper._element_resp_path('soh', ['Generic', 'Unity.resp'])
        self.assertTrue(path.endswith('Unity.resp'))
        with self.assertRaises(ValueError):
            helper._element_resp_path('soh', ['..', 'secrets.resp'])
        with self.assertRaises(ValueError):
            helper._element_resp_path('amplifier', ['Generic', 'Unity.resp'])

    def test_response_obj_reads_resp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        helper = NrlHelper(
            root_folder=os.path.join(tmp.name, 'root'),
            library_url='https://example.test/nrl.zip',
            media_root=os.path.join(tmp.name, 'media'),
        )
        element_dir = os.path.join(helper.content_folder, 'NRL', 'integrated', 'Gem')
        os.makedirs(element_dir)
        resp_path = os.path.join(element_dir, 'Gem.resp')
        with open(resp_path, 'w') as handle:
            handle.write('resp')
        response = Response()
        channel = MagicMock()
        channel.response = response
        station = MagicMock()
        station.channels = [channel]
        network = MagicMock()
        network.stations = [station]
        inventory = MagicMock()
        inventory.networks = [network]
        with patch('yasmine.app.helpers.nrl.nrl_helper.read_inventory', return_value=inventory) as read:
            with patch('yasmine.app.helpers.nrl.nrl_helper._normalize_response_units', side_effect=lambda item: item):
                loaded = helper.get_element_response_obj('integrated', ['Gem', 'Gem.resp'])
        self.assertIs(loaded, response)
        self.assertEqual(os.path.realpath(read.call_args.args[0]), os.path.realpath(resp_path))

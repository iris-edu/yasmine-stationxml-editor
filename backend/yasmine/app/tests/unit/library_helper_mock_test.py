# 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
# Offline library-helper tests: factory wiring and mocked catalog methods.

import unittest
from unittest.mock import MagicMock, patch

from yasmine.app.enums.library import LibraryTypeEnum
from yasmine.app.helpers.library_helper_factory import LibraryHelperFactory


class LibraryHelperMockTest(unittest.TestCase):

    def test_factory_returns_nrl_and_arol(self):
        factory = LibraryHelperFactory()
        nrl = factory.get_helper(LibraryTypeEnum.NRL)
        arol = factory.get_helper(LibraryTypeEnum.AROL)
        nrlv2 = factory.get_helper(LibraryTypeEnum.NRLV2_ONLINE)
        self.assertIsNotNone(nrl)
        self.assertIsNotNone(arol)
        self.assertIsNotNone(nrlv2)
        self.assertNotEqual(type(nrl), type(arol))
        with self.assertRaises(ValueError):
            factory.get_helper('unknown')

    def test_nrl_keys_can_be_mocked(self):
        helper = LibraryHelperFactory().get_helper(LibraryTypeEnum.NRL)
        helper.get_sensors_keys = MagicMock(return_value=[{'key': 'Guralp', 'children': []}])
        helper.get_dataloggers_keys = MagicMock(return_value=[{'key': 'REFTEK', 'children': []}])
        self.assertEqual(helper.get_sensors_keys()[0]['key'], 'Guralp')
        self.assertEqual(helper.get_dataloggers_keys()[0]['key'], 'REFTEK')

    @patch('yasmine.app.helpers.nrl.nrl_helper.NrlHelper.sync')
    def test_nrl_sync_is_patchable(self, mock_sync):
        helper = LibraryHelperFactory().get_helper(LibraryTypeEnum.NRL)
        helper.sync()
        mock_sync.assert_called()

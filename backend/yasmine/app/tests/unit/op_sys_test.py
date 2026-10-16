# 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
# Platform helper.

import unittest

from yasmine.app.utils.op_sys import is_windows


class OpSysTest(unittest.TestCase):

    def test_is_windows_is_bool(self):
        self.assertIsInstance(is_windows(), bool)

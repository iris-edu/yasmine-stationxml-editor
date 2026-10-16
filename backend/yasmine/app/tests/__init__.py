# 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
# Test package for Yasmine.
#
# Default discover loads unit/http/integration. GUI still needs
# YASMINE_TEST_GUI=1; downloads need YASMINE_TEST_NETWORK=1.

import os
import unittest

from yasmine.app.tests.common import gui_tests_enabled


def load_tests(loader, standard_tests, pattern):
    this_dir = os.path.dirname(__file__)
    top = getattr(loader, '_top_level_dir', None)
    suite = unittest.TestSuite()
    for sub in ('unit', 'http', 'integration'):
        suite.addTests(loader.discover(
            start_dir=os.path.join(this_dir, sub),
            pattern=pattern or '*_test.py',
            top_level_dir=top,
        ))
    if gui_tests_enabled():
        suite.addTests(loader.discover(
            start_dir=os.path.join(this_dir, 'gui'),
            pattern=pattern or '*_test.py',
            top_level_dir=top,
        ))
    return suite

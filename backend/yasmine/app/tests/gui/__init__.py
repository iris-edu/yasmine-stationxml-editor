# 2026-09-22, version 4.2.0-beta: ASGSR, Alexey Emanov
# Selenium GUI tests against a running app (opt-in).

import fnmatch
import os
import unittest

from yasmine.app.tests.common import gui_tests_enabled


def load_tests(loader, standard_tests, pattern):
    if not gui_tests_enabled():
        return unittest.TestSuite()
    this_dir = os.path.dirname(__file__)
    matched = pattern or '*_test.py'
    for name in sorted(os.listdir(this_dir)):
        if name.startswith('_') or not name.endswith('.py'):
            continue
        if not fnmatch.fnmatch(name, matched):
            continue
        module_name = 'yasmine.app.tests.gui.%s' % name[:-3]
        standard_tests.addTests(loader.loadTestsFromName(module_name))
    return standard_tests

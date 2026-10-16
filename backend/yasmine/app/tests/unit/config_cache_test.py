# 2026-09-27, version 4.4.0-beta: ASGSR, Alexey Emanov
# Settings saves clear the process config cache through the handler mixin.

import unittest

from yasmine.app.utils.facade import HandlerMixin


class _Application(object):
    def __init__(self):
        self.__config__ = {'general': {'name': 'old'}}

    def clear_config_cache(self):
        self.__config__ = None


class ConfigCacheTest(unittest.TestCase):

    def test_handler_clears_the_application_cache(self):
        application = _Application()
        HandlerMixin(application).clear_config_cache()
        self.assertIsNone(application.__config__)


if __name__ == '__main__':
    unittest.main()

# 2026-10-04, version 4.4.0-beta: ASGSR, Alexey Emanov
# Sample rate from last-stage decimation.

import unittest
from types import SimpleNamespace

from yasmine.app.utils.resp_import import sample_rate_from_response


class SampleRateFromResponseTest(unittest.TestCase):

    def test_divides_input_rate_by_factor(self):
        stage = SimpleNamespace(
            decimation_factor=4,
            decimation_input_sample_rate=400.0,
        )
        response = SimpleNamespace(response_stages=[stage])
        self.assertEqual(sample_rate_from_response(response), 100.0)

    def test_missing_or_unsafe_decimation_returns_none(self):
        self.assertIsNone(sample_rate_from_response(None))
        self.assertIsNone(sample_rate_from_response(SimpleNamespace(response_stages=[])))
        self.assertIsNone(sample_rate_from_response(SimpleNamespace(response_stages=[
            SimpleNamespace(decimation_factor=None, decimation_input_sample_rate=100.0),
        ])))
        self.assertIsNone(sample_rate_from_response(SimpleNamespace(response_stages=[
            SimpleNamespace(decimation_factor=0, decimation_input_sample_rate=100.0),
        ])))
        self.assertIsNone(sample_rate_from_response(SimpleNamespace(response_stages=[
            SimpleNamespace(decimation_factor=2, decimation_input_sample_rate=None),
        ])))


if __name__ == '__main__':
    unittest.main()

# 2026-09-19, version 4.2.0-beta: ASGSR, Alexey Emanov
# SSRF URL guard unit tests.

import unittest
from unittest.mock import patch

from yasmine.app.utils.url_guard import UrlGuardError, validate_url


class UrlGuardTest(unittest.TestCase):

    def test_rejects_file_scheme(self):
        with self.assertRaises(UrlGuardError):
            validate_url('file:///etc/passwd')

    def test_rejects_localhost(self):
        with self.assertRaises(UrlGuardError):
            validate_url('http://127.0.0.1/secret')

    def test_rejects_decimal_ip(self):
        with self.assertRaises(UrlGuardError):
            validate_url('https://2130706433/nrl')

    @patch('yasmine.app.utils.url_guard.socket.getaddrinfo', return_value=[(0, 0, 0, '', ('1.1.1.1', 443))])
    def test_accepts_allowlisted_https(self, _mock_dns):
        validate_url('https://service.earthscope.org/irisws/nrl/1/')

    @patch('yasmine.app.utils.url_guard.socket.getaddrinfo', return_value=[(0, 0, 0, '', ('10.0.0.8', 443))])
    def test_rejects_dns_rebinding_to_private(self, _mock_dns):
        with self.assertRaises(UrlGuardError):
            validate_url('https://service.earthscope.org/irisws/nrl/1/')

    @patch('yasmine.app.utils.url_guard.socket.getaddrinfo', return_value=[(0, 0, 0, '', ('10.7.0.15', 8900))])
    def test_allow_private_hostnames_skips_resolved_ip(self, _mock_dns):
        validate_url(
            'http://vh07.gsn:8900/nrl/1',
            schemes=('http', 'https'),
            require_allowlist=False,
            allow_private_hostnames=True,
        )
        _mock_dns.assert_not_called()

    def test_allow_private_hostnames_still_rejects_raw_private_ip(self):
        with self.assertRaises(UrlGuardError):
            validate_url(
                'http://192.168.1.1/nrl/1',
                schemes=('http', 'https'),
                require_allowlist=False,
                allow_private_hostnames=True,
            )

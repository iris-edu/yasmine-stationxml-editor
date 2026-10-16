# 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
# ETag helper: new tag, unchanged tag, and persist.

import os
import tempfile
import unittest
from unittest.mock import patch

from yasmine.app.helpers.etag_helper import EtagHelper


class _Head(object):
    def __init__(self, etag, status_code=200, last_modified=None):
        self.status_code = status_code
        self.headers = {}
        if etag is not None:
            self.headers['etag'] = etag
        if last_modified:
            self.headers['last-modified'] = last_modified


class EtagHelperTest(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.mkdtemp()

    def tearDown(self):
        for name in os.listdir(self.folder):
            os.remove(os.path.join(self.folder, name))
        os.rmdir(self.folder)

    @patch('yasmine.app.helpers.etag_helper.requests.head', return_value=_Head('"abc"'))
    def test_first_check_is_new(self, _head):
        helper = EtagHelper(self.folder, 'https://example.test/lib.zip')
        self.assertTrue(helper.is_new_etag_available())
        helper.save_etag()
        self.assertFalse(helper.is_new_etag_available())

    @patch('yasmine.app.helpers.etag_helper.requests.head', return_value=_Head('"new"'))
    def test_changed_etag_is_new(self, _head):
        helper = EtagHelper(self.folder, 'https://example.test/lib.zip')
        with open(os.path.join(self.folder, 'etag.txt'), 'wt') as handle:
            handle.write('"old"')
        self.assertTrue(helper.is_new_etag_available())
        helper.save_etag()
        with open(os.path.join(self.folder, 'etag.txt'), 'rt') as handle:
            self.assertEqual(handle.read(), '"new"')

    @patch('yasmine.app.helpers.etag_helper.requests.head', return_value=_Head(None, status_code=503))
    def test_failed_head_does_not_count_as_a_new_archive(self, _head):
        helper = EtagHelper(self.folder, 'https://example.test/lib.zip')
        with open(os.path.join(self.folder, 'etag.txt'), 'wt') as handle:
            handle.write('"abc"')
        self.assertFalse(helper.is_new_etag_available())

# 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
# Zip-slip and size-cap tests for safe_extractall.

import io
import os
import tempfile
import unittest
import zipfile

from yasmine.app.utils.zip_safe import UnsafeZipError, safe_extract_flat, safe_extractall


class ZipSafeTest(unittest.TestCase):

    def test_rejects_parent_directory_entry(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('../evil.txt', 'pwned')
        buf.seek(0)
        dest = tempfile.mkdtemp()
        with zipfile.ZipFile(buf) as zf:
            with self.assertRaises(UnsafeZipError):
                safe_extractall(zf, dest)
        self.assertFalse(os.path.exists(os.path.join(os.path.dirname(dest), 'evil.txt')))

    def test_rejects_absolute_path(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('/tmp/evil.txt', 'pwned')
        buf.seek(0)
        dest = tempfile.mkdtemp()
        with zipfile.ZipFile(buf) as zf:
            with self.assertRaises(UnsafeZipError):
                safe_extractall(zf, dest)

    def test_rejects_windows_drive_path(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('C:/Windows/evil.txt', 'pwned')
        buf.seek(0)
        dest = tempfile.mkdtemp()
        with zipfile.ZipFile(buf) as zf:
            with self.assertRaises(UnsafeZipError):
                safe_extractall(zf, dest)

    def test_rejects_too_many_entries(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            for i in range(5):
                zf.writestr('f%s.txt' % i, 'x')
        buf.seek(0)
        dest = tempfile.mkdtemp()
        with zipfile.ZipFile(buf) as zf:
            with self.assertRaises(UnsafeZipError):
                safe_extractall(zf, dest, max_entries=3)

    def test_extracts_normal_file(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('ok.yaml', 'a: 1\n')
        buf.seek(0)
        dest = tempfile.mkdtemp()
        with zipfile.ZipFile(buf) as zf:
            safe_extractall(zf, dest)
        self.assertTrue(os.path.isfile(os.path.join(dest, 'ok.yaml')))

    def test_size_limit(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('big.bin', b'x' * 2048)
        buf.seek(0)
        dest = tempfile.mkdtemp()
        with zipfile.ZipFile(buf) as zf:
            with self.assertRaises(UnsafeZipError):
                safe_extractall(zf, dest, max_bytes=100)

    def test_flat_extract_keeps_basename_inside_dest(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('../evil.yaml', 'stolen: 1\n')
        buf.seek(0)
        dest = tempfile.mkdtemp()
        with zipfile.ZipFile(buf) as zf:
            safe_extract_flat(zf, dest)
        self.assertTrue(os.path.isfile(os.path.join(dest, 'evil.yaml')))
        self.assertFalse(os.path.exists(os.path.join(os.path.dirname(dest), 'evil.yaml')))

    def test_flat_extract_size_limit(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('big.bin', b'x' * 2048)
        buf.seek(0)
        dest = tempfile.mkdtemp()
        with zipfile.ZipFile(buf) as zf:
            with self.assertRaises(UnsafeZipError):
                safe_extract_flat(zf, dest, max_bytes=100)

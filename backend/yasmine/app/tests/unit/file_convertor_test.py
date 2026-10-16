# 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
# SSRF, zip-slip and YAML loader tests for FileConvertorService.

import io
import json
import os
import shutil
import tempfile
import unittest
import zipfile
from unittest.mock import patch

import yaml

from yasmine.app.services.file_convertor_service import FileConvertorService


class FileConvertorServiceTest(unittest.TestCase):

    def test_convert_from_url_rejects_file_scheme(self):
        with self.assertRaises(ValueError):
            FileConvertorService().convert_from_url('file:///etc/passwd')

    def test_convert_from_url_rejects_localhost(self):
        with self.assertRaises(ValueError):
            FileConvertorService().convert_from_url('http://127.0.0.1/secret.zip')

    def test_convert_from_url_rejects_private_host(self):
        with self.assertRaises(ValueError):
            FileConvertorService().convert_from_url('https://192.168.1.1/nrl.zip')

    def test_zip_slip_does_not_write_outside_target(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('../evil.txt', 'pwned')
            zf.writestr('ok.yaml', 'a: 1\n')
        buf.seek(0)
        with zipfile.ZipFile(buf) as zf:
            with self.assertRaises(ValueError):
                FileConvertorService(flattern=False).convert_from_zip(zf)

    def test_flatten_zip_does_not_escape_target(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('../evil.yaml', 'stolen: 1\n')
            zf.writestr('ok.yaml', 'a: 1\n')
        buf.seek(0)
        with zipfile.ZipFile(buf) as zf:
            folder = FileConvertorService(flattern=True).convert_from_zip(zf)
        self.assertTrue(os.path.isdir(folder))
        self.assertFalse(os.path.exists(os.path.join(os.path.dirname(folder), 'evil.yaml')))

    def test_user_library_uses_safe_yaml_loader(self):
        service = FileConvertorService(flattern=True, is_full_loader=True)
        tmp = tempfile.mkdtemp()
        try:
            path = os.path.join(tmp, 'x.yaml')
            with open(path, 'w') as handle:
                handle.write('!!python/object/apply:os.system ["echo pwned"]\n')
            with patch('yasmine.app.services.file_convertor_service.yaml.load', wraps=yaml.load) as mocked:
                with self.assertRaises((yaml.YAMLError, Exception)):
                    service.convert_from_folder(tmp)
                self.assertTrue(mocked.called)
                _args, kwargs = mocked.call_args
                self.assertIs(kwargs.get('Loader'), yaml.SafeLoader)
        finally:
            pass

    def test_yaml_dates_become_iso_strings(self):
        src = tempfile.mkdtemp()
        try:
            with open(os.path.join(src, 'guralp.yaml'), 'w') as handle:
                handle.write(
                    'start_time: 1995-06-27\n'
                    'end_time: 2005-06-07\n'
                )
            folder = FileConvertorService().convert_from_folder(src)
            try:
                with open(os.path.join(folder, 'guralp.json')) as handle:
                    payload = json.load(handle)
            finally:
                shutil.rmtree(folder)
        finally:
            shutil.rmtree(src)
        self.assertEqual(payload['start_time'], '1995-06-27')
        self.assertEqual(payload['end_time'], '2005-06-07')

    def test_unserializable_yaml_does_not_leave_partial_json(self):
        src = tempfile.mkdtemp()
        try:
            with open(os.path.join(src, 'bad.yaml'), 'w') as handle:
                handle.write('name: UNSERIALIZABLE\n')
            with open(os.path.join(src, 'ok.yaml'), 'w') as handle:
                handle.write('name: kept\n')
            real_load = yaml.load

            def load(stream, Loader=None):
                raw = stream.read()
                text = raw.decode() if isinstance(raw, bytes) else raw
                if 'UNSERIALIZABLE' in text:
                    return {'blob': object()}
                return real_load(io.StringIO(text), Loader=Loader)

            with patch('yasmine.app.services.file_convertor_service.yaml.load', side_effect=load):
                folder = FileConvertorService().convert_from_folder(src)
            try:
                self.assertFalse(os.path.exists(os.path.join(folder, 'bad.json')))
                with open(os.path.join(folder, 'ok.json')) as handle:
                    self.assertEqual(json.load(handle)['name'], 'kept')
            finally:
                shutil.rmtree(folder)
        finally:
            shutil.rmtree(src)

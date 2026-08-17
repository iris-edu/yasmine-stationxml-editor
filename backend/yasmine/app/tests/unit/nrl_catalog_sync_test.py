# ****************************************************************************
#
# Unit tests for NRL Offline catalog-based update check.
#
# NRL Offline update check (2026): ASGSR, Alexey Emanov.
#
# ****************************************************************************/

import io
import os
import tempfile
import unittest
import zipfile
from datetime import datetime
from unittest.mock import MagicMock, patch

import requests

from yasmine.app.helpers.nrl.nrl_catalog_update import (
    NrlCatalogUpdateError,
    NrlCatalogUpdateHelper,
)
from yasmine.app.helpers.nrl.nrl_helper import NrlHelper


CATALOG_HEADER = (
    '"Element","Manufacturer","Model","Description","Instconfig"\n'
)
CATALOG_ROW = (
    '"sensor","Guralp","CMG-3T","test",'
    '"sensor_Guralp_CMG-3T_LP120_HF50_SG20000_STgroundVel"\n'
)
CATALOG_ROW_2 = (
    '"datalogger","Quanterra","Q330","test2",'
    '"datalogger_Quanterra_Q330_PG1_FR100"\n'
)


def _make_zip_bytes(marker='v1'):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        zf.writestr('NRL/README', 'nrl-archive-%s\n' % marker)
        zf.writestr('NRL/sensors/.keep', '')
        zf.writestr('NRL/dataloggers/.keep', '')
    return buf.getvalue()


def _make_invalid_zip_bytes():
    return b'not-a-zip-file'


class FakeResponse:
    def __init__(self, status_code=200, text='', content=b'', raise_exc=None):
        self.status_code = status_code
        self.text = text
        self.content = content
        self._raise_exc = raise_exc

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError('HTTP %s' % self.status_code)


class FakeSession:
    def __init__(self, handlers):
        """handlers: list of callables(url, params) -> FakeResponse or Exception."""
        self.handlers = list(handlers)
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append({'url': url, 'params': params, 'timeout': timeout})
        if not self.handlers:
            raise AssertionError('Unexpected GET %s' % url)
        handler = self.handlers.pop(0)
        result = handler(url, params)
        if isinstance(result, Exception):
            raise result
        return result


class NrlCatalogUpdateHelperTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_save_and_read_last_successful_download_date(self):
        helper = NrlCatalogUpdateHelper(
            self.root, utcnow_fn=lambda: datetime(2026, 8, 17, 13, 42, 17)
        )
        helper.save_last_successful_download_date()
        self.assertEqual(
            helper.get_last_successful_download_date(), '2026-08-17'
        )

    def test_header_only_means_no_updates(self):
        helper = NrlCatalogUpdateHelper(self.root)
        self.assertFalse(helper._catalog_has_data_rows(CATALOG_HEADER))

    def test_one_data_row_means_updates(self):
        helper = NrlCatalogUpdateHelper(self.root)
        self.assertTrue(
            helper._catalog_has_data_rows(CATALOG_HEADER + CATALOG_ROW)
        )

    def test_multiple_data_rows_means_updates(self):
        helper = NrlCatalogUpdateHelper(self.root)
        text = CATALOG_HEADER + CATALOG_ROW + CATALOG_ROW_2
        self.assertTrue(helper._catalog_has_data_rows(text))

    def test_invalid_header_is_error(self):
        helper = NrlCatalogUpdateHelper(self.root)
        with self.assertRaises(NrlCatalogUpdateError):
            helper._catalog_has_data_rows('"A","B"\n')

    def test_empty_response_is_error_not_no_updates(self):
        helper = NrlCatalogUpdateHelper(self.root)
        with self.assertRaises(NrlCatalogUpdateError):
            helper._catalog_has_data_rows('')

    def test_has_updates_since_builds_expected_query(self):
        session = FakeSession([
            lambda url, params: FakeResponse(text=CATALOG_HEADER)
        ])
        helper = NrlCatalogUpdateHelper(
            self.root,
            catalog_url='https://example.test/catalog',
            session=session,
            timeout=12,
        )
        self.assertFalse(helper.has_updates_since('2026-08-17'))
        self.assertEqual(len(session.calls), 1)
        call = session.calls[0]
        self.assertEqual(call['url'], 'https://example.test/catalog')
        self.assertEqual(call['timeout'], 12)
        self.assertEqual(call['params']['updatedsince'], '2026-08-17')
        self.assertEqual(call['params']['element'], '*')
        self.assertEqual(call['params']['format'], 'text')
        self.assertEqual(call['params']['level'], 'configuration')

    def test_catalog_http_error(self):
        session = FakeSession([
            lambda url, params: FakeResponse(status_code=500, text='err')
        ])
        helper = NrlCatalogUpdateHelper(self.root, session=session)
        with self.assertRaises(NrlCatalogUpdateError) as ctx:
            helper.has_updates_since('2026-08-01')
        self.assertIn('HTTP 500', str(ctx.exception))

    def test_catalog_timeout(self):
        session = FakeSession([
            lambda url, params: requests.Timeout('timed out')
        ])
        helper = NrlCatalogUpdateHelper(self.root, session=session)
        with self.assertRaises(NrlCatalogUpdateError) as ctx:
            helper.has_updates_since('2026-08-01')
        self.assertIn('timeout', str(ctx.exception))


class NrlHelperCatalogSyncTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.tmp.name, 'nrl')
        self.media = os.path.join(self.tmp.name, 'media')
        os.makedirs(self.root)
        os.makedirs(self.media)
        self.fixed_now = datetime(2026, 8, 17, 13, 42, 17)

    def tearDown(self):
        self.tmp.cleanup()

    def _helper(self, session):
        return NrlHelper(
            root_folder=self.root,
            library_url='https://example.test/nrl.zip',
            catalog_url='https://example.test/catalog',
            timeout=30,
            media_root=self.media,
            utcnow_fn=lambda: self.fixed_now,
            session=session,
        )

    def _seed_existing_library(self, marker='old', date='2026-08-17'):
        nrl_dir = os.path.join(self.root, 'content', 'NRL')
        os.makedirs(nrl_dir)
        with open(os.path.join(nrl_dir, 'README'), 'w') as f:
            f.write(marker)
        with open(
            os.path.join(self.root, 'last_successful_download_date.txt'), 'w'
        ) as f:
            f.write(date)
        with open(os.path.join(self.root, 'sensors.json'), 'wb') as f:
            f.write(b'old-sensors')
        with open(os.path.join(self.root, 'dataloggers.json'), 'wb') as f:
            f.write(b'old-dataloggers')

    def _patch_prepare(self):
        fake_nrl = MagicMock()
        fake_nrl.sensors = MagicMock()
        fake_nrl.dataloggers = MagicMock()
        return patch.multiple(
            'yasmine.app.helpers.nrl.nrl_helper',
            NRL=MagicMock(return_value=fake_nrl),
            NrlKeyCreator=MagicMock(
                return_value=MagicMock(
                    create_keys=MagicMock(return_value=([], []))
                )
            ),
        )

    def test_initial_install_skips_catalog_and_downloads_zip(self):
        zip_bytes = _make_zip_bytes('initial')
        session = FakeSession([
            lambda url, params: FakeResponse(content=zip_bytes),
        ])
        helper = self._helper(session)
        with self._patch_prepare():
            helper.sync()
        self.assertTrue(
            os.path.isdir(os.path.join(self.root, 'content', 'NRL'))
        )
        self.assertEqual(
            helper.catalog_helper.get_last_successful_download_date(),
            '2026-08-17',
        )
        self.assertEqual(len(session.calls), 1)
        self.assertIn('nrl.zip', session.calls[0]['url'])

    def test_no_updates_header_only_skips_download(self):
        self._seed_existing_library()
        session = FakeSession([
            lambda url, params: FakeResponse(text=CATALOG_HEADER),
        ])
        helper = self._helper(session)
        helper.sync()
        self.assertEqual(len(session.calls), 1)
        self.assertIn('catalog', session.calls[0]['url'])
        with open(os.path.join(self.root, 'content', 'NRL', 'README')) as f:
            self.assertEqual(f.read(), 'old')
        self.assertEqual(
            helper.catalog_helper.get_last_successful_download_date(),
            '2026-08-17',
        )

    def test_updates_available_triggers_download(self):
        self._seed_existing_library()
        zip_bytes = _make_zip_bytes('new')
        session = FakeSession([
            lambda url, params: FakeResponse(
                text=CATALOG_HEADER + CATALOG_ROW
            ),
            lambda url, params: FakeResponse(content=zip_bytes),
        ])
        helper = self._helper(session)
        with self._patch_prepare():
            helper.sync()
        self.assertEqual(len(session.calls), 2)
        with open(os.path.join(self.root, 'content', 'NRL', 'README')) as f:
            self.assertIn('nrl-archive-new', f.read())

    def test_multiple_catalog_rows_single_download(self):
        self._seed_existing_library()
        zip_bytes = _make_zip_bytes('multi')
        session = FakeSession([
            lambda url, params: FakeResponse(
                text=CATALOG_HEADER + CATALOG_ROW + CATALOG_ROW_2
            ),
            lambda url, params: FakeResponse(content=zip_bytes),
        ])
        helper = self._helper(session)
        with self._patch_prepare():
            helper.sync()
        zip_calls = [c for c in session.calls if 'nrl.zip' in c['url']]
        self.assertEqual(len(zip_calls), 1)

    def test_catalog_http_error_preserves_archive(self):
        self._seed_existing_library()
        session = FakeSession([
            lambda url, params: FakeResponse(status_code=503, text='down'),
        ])
        helper = self._helper(session)
        helper.sync()
        with open(os.path.join(self.root, 'content', 'NRL', 'README')) as f:
            self.assertEqual(f.read(), 'old')
        self.assertEqual(
            helper.catalog_helper.get_last_successful_download_date(),
            '2026-08-17',
        )
        self.assertEqual(len(session.calls), 1)

    def test_invalid_catalog_response_is_error_not_no_updates(self):
        self._seed_existing_library()
        session = FakeSession([
            lambda url, params: FakeResponse(text='not,csv,header\n1,2,3\n'),
        ])
        helper = self._helper(session)
        helper.sync()
        # No ZIP download attempted.
        self.assertEqual(len(session.calls), 1)
        with open(os.path.join(self.root, 'content', 'NRL', 'README')) as f:
            self.assertEqual(f.read(), 'old')
        self.assertEqual(
            helper.catalog_helper.get_last_successful_download_date(),
            '2026-08-17',
        )

    def test_zip_download_failure_keeps_existing_library(self):
        self._seed_existing_library()
        session = FakeSession([
            lambda url, params: FakeResponse(
                text=CATALOG_HEADER + CATALOG_ROW
            ),
            lambda url, params: FakeResponse(status_code=500, content=b''),
        ])
        helper = self._helper(session)
        helper.sync()
        with open(os.path.join(self.root, 'content', 'NRL', 'README')) as f:
            self.assertEqual(f.read(), 'old')
        self.assertEqual(
            helper.catalog_helper.get_last_successful_download_date(),
            '2026-08-17',
        )

    def test_invalid_zip_keeps_existing_library(self):
        self._seed_existing_library()
        session = FakeSession([
            lambda url, params: FakeResponse(
                text=CATALOG_HEADER + CATALOG_ROW
            ),
            lambda url, params: FakeResponse(
                content=_make_invalid_zip_bytes()
            ),
        ])
        helper = self._helper(session)
        helper.sync()
        with open(os.path.join(self.root, 'content', 'NRL', 'README')) as f:
            self.assertEqual(f.read(), 'old')
        self.assertEqual(
            helper.catalog_helper.get_last_successful_download_date(),
            '2026-08-17',
        )

    def test_successful_update_sets_last_download_date_utc(self):
        self._seed_existing_library(date='2026-08-01')
        self.fixed_now = datetime(2026, 8, 17, 13, 42, 17)
        zip_bytes = _make_zip_bytes('ok')
        session = FakeSession([
            lambda url, params: FakeResponse(
                text=CATALOG_HEADER + CATALOG_ROW
            ),
            lambda url, params: FakeResponse(content=zip_bytes),
        ])
        helper = self._helper(session)
        with self._patch_prepare():
            helper.sync()
        self.assertEqual(
            helper.catalog_helper.get_last_successful_download_date(),
            '2026-08-17',
        )

    def test_same_day_uses_same_updatedsince_date(self):
        self._seed_existing_library(date='2026-08-17')
        session = FakeSession([
            lambda url, params: FakeResponse(text=CATALOG_HEADER),
        ])
        helper = self._helper(session)
        helper.sync()
        self.assertEqual(
            session.calls[0]['params']['updatedsince'], '2026-08-17'
        )

    def test_prepare_failure_rolls_back_existing_library(self):
        self._seed_existing_library()
        zip_bytes = _make_zip_bytes('bad-prepare')
        session = FakeSession([
            lambda url, params: FakeResponse(
                text=CATALOG_HEADER + CATALOG_ROW
            ),
            lambda url, params: FakeResponse(content=zip_bytes),
        ])
        helper = self._helper(session)
        with patch(
            'yasmine.app.helpers.nrl.nrl_helper.NRL',
            side_effect=RuntimeError('bad nrl'),
        ):
            helper.sync()
        with open(os.path.join(self.root, 'content', 'NRL', 'README')) as f:
            self.assertEqual(f.read(), 'old')
        self.assertEqual(
            helper.catalog_helper.get_last_successful_download_date(),
            '2026-08-17',
        )

    def test_unknown_date_with_existing_archive_forces_download(self):
        nrl_dir = os.path.join(self.root, 'content', 'NRL')
        os.makedirs(nrl_dir)
        with open(os.path.join(nrl_dir, 'README'), 'w') as f:
            f.write('legacy')
        zip_bytes = _make_zip_bytes('init-date')
        session = FakeSession([
            lambda url, params: FakeResponse(content=zip_bytes),
        ])
        helper = self._helper(session)
        with self._patch_prepare():
            helper.sync()
        self.assertEqual(
            helper.catalog_helper.get_last_successful_download_date(),
            '2026-08-17',
        )
        self.assertEqual(len(session.calls), 1)
        self.assertIn('nrl.zip', session.calls[0]['url'])


if __name__ == '__main__':
    unittest.main()

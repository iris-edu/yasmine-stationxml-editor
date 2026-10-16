# 2026-09-27, version 4.4.0-beta: ASGSR, Alexey Emanov
# ****************************************************************************
#
# Startup logs must say when HTTP is ready and how NRL/AROL sync ended.
#
# ****************************************************************************/

import logging
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from yasmine.app.run import Application, runserver
from yasmine.app.settings import STATIONXML_UPLOAD_MAX_BYTES


class StartupLogTest(unittest.TestCase):

    def _messages(self, records):
        return [record.getMessage() for record in records]

    def test_http_ready_is_logged_after_listen(self):
        with patch('yasmine.app.run.Application') as application_cls, \
                patch('yasmine.app.run.tornado.ioloop.IOLoop') as ioloop_cls:
            with self.assertLogs('yasmine.app.run', level='INFO') as logs:
                runserver(False, host='127.0.0.1', port=8080)
        application_cls.assert_called_once_with(False)
        application_cls.return_value.listen.assert_called_once_with(
            port=8080,
            address='127.0.0.1',
            max_body_size=STATIONXML_UPLOAD_MAX_BYTES,
            max_buffer_size=STATIONXML_UPLOAD_MAX_BYTES,
        )
        ioloop_cls.instance.return_value.start.assert_called_once_with()
        messages = self._messages(logs.records)
        self.assertIn(
            'HTTP listening on 127.0.0.1:8080; the interface can be opened',
            messages,
        )
        self.assertFalse(any('catalog' in message.lower() for message in messages))
        self.assertFalse(any('NRL' in message for message in messages))

    def test_empty_host_is_logged_as_all_interfaces(self):
        with patch('yasmine.app.run.Application'), \
                patch('yasmine.app.run.tornado.ioloop.IOLoop'):
            with self.assertLogs('yasmine.app.run', level='INFO') as logs:
                runserver(False, host='', port=80)
        self.assertIn(
            'HTTP listening on 0.0.0.0:80; the interface can be opened',
            self._messages(logs.records),
        )

    def test_http_ready_is_not_logged_when_listen_fails(self):
        records = []
        handler = logging.Handler()
        handler.emit = records.append
        app_logger = logging.getLogger('yasmine.app.run')
        app_logger.addHandler(handler)
        previous_level = app_logger.level
        app_logger.setLevel(logging.INFO)
        try:
            with patch('yasmine.app.run.Application') as application_cls, \
                    patch('yasmine.app.run.tornado.ioloop.IOLoop'):
                application_cls.return_value.listen.side_effect = OSError('address in use')
                with self.assertRaises(OSError):
                    runserver(False, host='127.0.0.1', port=9)
        finally:
            app_logger.removeHandler(handler)
            app_logger.setLevel(previous_level)
        self.assertFalse(any(
            'HTTP listening' in record.getMessage() for record in records
        ))

    def test_nrl_sync_skipped_when_disabled(self):
        app = SimpleNamespace(config=SimpleNamespace(get=lambda group, name: False))
        with patch('yasmine.app.run.LibraryHelperFactory') as factory:
            with self.assertLogs('yasmine.app.run', level='INFO') as logs:
                Application._sync_nrl_blocking(app)
        factory.assert_not_called()
        self.assertEqual(['NRL sync skipped'], self._messages(logs.records))
        self.assertEqual(logging.INFO, logs.records[0].levelno)

    def test_nrl_sync_finished(self):
        app = SimpleNamespace(
            sync_nrl_started=False,
            config=SimpleNamespace(get=lambda group, name: True),
        )
        with patch('yasmine.app.run.LibraryHelperFactory') as factory:
            with self.assertLogs('yasmine.app.run', level='INFO') as logs:
                Application._sync_nrl_blocking(app)
        factory.return_value.get_helper.return_value.sync.assert_called_once_with()
        self.assertTrue(app.sync_nrl_started)
        self.assertEqual(['NRL sync finished'], self._messages(logs.records))

    def test_nrl_sync_failed_keeps_the_exception(self):
        app = SimpleNamespace(
            sync_nrl_started=False,
            config=SimpleNamespace(get=lambda group, name: True),
        )
        with patch('yasmine.app.run.LibraryHelperFactory') as factory:
            factory.return_value.get_helper.return_value.sync.side_effect = RuntimeError('boom')
            with self.assertLogs('yasmine.app.run', level='INFO') as logs:
                Application._sync_nrl_blocking(app)
        self.assertFalse(app.sync_nrl_started)
        messages = self._messages(logs.records)
        self.assertIn('NRL archive download/update failed', messages)
        self.assertIn('NRL sync failed', messages)
        self.assertNotIn('NRL sync finished', messages)
        failed = next(
            record for record in logs.records
            if record.getMessage() == 'NRL archive download/update failed'
        )
        self.assertIsInstance(failed.exc_info[1], RuntimeError)
        summary = next(
            record for record in logs.records
            if record.getMessage() == 'NRL sync failed'
        )
        self.assertEqual(logging.INFO, summary.levelno)

    def test_arol_sync_finished(self):
        app = SimpleNamespace(sync_ial_started=False)
        with patch('yasmine.app.run.LibraryHelperFactory') as factory:
            with self.assertLogs('yasmine.app.run', level='INFO') as logs:
                Application._sync_ial_blocking(app)
        factory.return_value.get_helper.return_value.sync.assert_called_once_with()
        self.assertTrue(app.sync_ial_started)
        self.assertEqual(['AROL sync finished'], self._messages(logs.records))

    def test_arol_sync_failed_keeps_the_exception(self):
        app = SimpleNamespace(sync_ial_started=False)
        with patch('yasmine.app.run.LibraryHelperFactory') as factory:
            factory.return_value.get_helper.return_value.sync.side_effect = RuntimeError('boom')
            with self.assertLogs('yasmine.app.run', level='INFO') as logs:
                Application._sync_ial_blocking(app)
        self.assertFalse(app.sync_ial_started)
        messages = self._messages(logs.records)
        self.assertIn('AROL library sync failed', messages)
        self.assertIn('AROL sync failed', messages)
        self.assertNotIn('AROL sync finished', messages)
        failed = next(
            record for record in logs.records
            if record.getMessage() == 'AROL library sync failed'
        )
        self.assertIsInstance(failed.exc_info[1], RuntimeError)

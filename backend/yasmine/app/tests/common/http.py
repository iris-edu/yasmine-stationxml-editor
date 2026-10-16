# 2026-09-18, version 4.1.3-beta: ASGSR, Alexey Emanov
# HTTP test helper: isolated sqlite + Application without NRL/AROL scheduler.

import json
import os
import shutil
import tempfile
from unittest.mock import patch

from tornado.testing import AsyncHTTPTestCase

from yasmine.app.tests.integration.utils.integration_util import migrate_db, remove_db


class YasmineHTTPTestCase(AsyncHTTPTestCase):
    """AsyncHTTPTestCase bound to a throwaway sqlite database."""

    def setUp(self):
        self._db_name = '%s_%s' % (self.__class__.__name__, os.getpid())
        migrate_db(self._db_name)
        super(YasmineHTTPTestCase, self).setUp()

    def tearDown(self):
        super(YasmineHTTPTestCase, self).tearDown()
        try:
            remove_db(self._db_name)
        except OSError:
            pass

    def get_app(self):
        from yasmine.app.run import Application
        return Application(debug=False, enable_scheduler=False)

    def fetch_json(self, path, method='GET', body=None, headers=None, **kwargs):
        req_headers = {'Content-Type': 'application/json'}
        if headers:
            req_headers.update(headers)
        if body is not None and not isinstance(body, (bytes, str)):
            body = json.dumps(body)
        response = self.fetch(path, method=method, body=body, headers=req_headers, **kwargs)
        payload = None
        if response.body:
            try:
                payload = json.loads(response.body.decode('utf-8'))
            except ValueError:
                payload = response.body.decode('utf-8', errors='replace')
        return response, payload

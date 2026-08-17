# ****************************************************************************
#
# NRL Offline update check via catalog?updatedsince=...
#
# NRLv2 online / NRL Offline update check (2026): ASGSR, Alexey Emanov.
#
# ****************************************************************************/


import csv
import io
import logging
import os
import tempfile

import requests

from yasmine.app.settings import (
    NRL_CATALOG_URL,
    NRL_HTTP_TIMEOUT,
    NRL_LAST_DOWNLOAD_DATE_FILE,
)
from yasmine.app.utils.date import get_utcnow_naive


CATALOG_EXPECTED_HEADER = [
    'Element',
    'Manufacturer',
    'Model',
    'Description',
    'Instconfig',
]


class NrlCatalogUpdateError(Exception):
    """Raised when the NRL catalog update check fails."""


class NrlCatalogUpdateHelper:
    """Persist last successful download date and check NRL catalog for updates."""

    def __init__(
        self,
        root_folder,
        catalog_url=None,
        timeout=None,
        utcnow_fn=None,
        session=None,
        logger=None,
    ):
        self.root_folder = root_folder
        self.catalog_url = catalog_url or NRL_CATALOG_URL
        self.timeout = timeout if timeout is not None else NRL_HTTP_TIMEOUT
        self.utcnow_fn = utcnow_fn or get_utcnow_naive
        self.session = session or requests
        self.logger = logger or logging.getLogger(__name__)
        self.date_file = os.path.join(
            root_folder, NRL_LAST_DOWNLOAD_DATE_FILE
        )
        os.makedirs(root_folder, exist_ok=True)

    def get_last_successful_download_date(self):
        if not os.path.exists(self.date_file):
            return None
        try:
            with open(self.date_file, 'rt', encoding='utf-8') as f:
                value = f.read().strip()
        except OSError as err:
            raise NrlCatalogUpdateError(
                'Cannot read last successful download date: %s' % err
            )
        if not value:
            return None
        if len(value) != 10 or value[4] != '-' or value[7] != '-':
            raise NrlCatalogUpdateError(
                'Invalid last successful download date: %r' % value
            )
        try:
            year, month, day = value.split('-')
            int(year), int(month), int(day)
        except ValueError:
            raise NrlCatalogUpdateError(
                'Invalid last successful download date: %r' % value
            )
        return value

    def save_last_successful_download_date(self, date_str=None):
        if date_str is None:
            date_str = self.utcnow_fn().strftime('%Y-%m-%d')
        os.makedirs(self.root_folder, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(
            prefix='nrl_last_download_',
            suffix='.tmp',
            dir=self.root_folder,
        )
        try:
            with os.fdopen(fd, 'wt', encoding='utf-8') as f:
                f.write(date_str)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self.date_file)
        except Exception:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass
            raise

    def has_updates_since(self, updatedsince):
        """Return True if catalog has at least one data row after updatedsince.

        Raises NrlCatalogUpdateError on HTTP/network/parse failures.
        """
        self.logger.info('Checking NRL updates since %s', updatedsince)
        params = {
            'element': '*',
            'format': 'text',
            'level': 'configuration',
            'updatedsince': updatedsince,
        }
        try:
            response = self.session.get(
                self.catalog_url,
                params=params,
                timeout=self.timeout,
            )
        except requests.Timeout as err:
            raise NrlCatalogUpdateError('timeout: %s' % err)
        except requests.RequestException as err:
            raise NrlCatalogUpdateError('connection error: %s' % err)

        if response.status_code != 200:
            raise NrlCatalogUpdateError(
                'HTTP %s' % response.status_code
            )

        try:
            text = response.text
        except Exception as err:
            raise NrlCatalogUpdateError(
                'cannot decode catalog response: %s' % err
            )

        return self._catalog_has_data_rows(text)

    @staticmethod
    def _normalize_header(row):
        return [cell.strip().strip('"') for cell in row]

    def _catalog_has_data_rows(self, text):
        if text is None:
            raise NrlCatalogUpdateError('empty catalog response')

        # Do not treat header-only as empty string / no content.
        stream = io.StringIO(text)
        try:
            reader = csv.reader(stream)
            try:
                header = next(reader)
            except StopIteration:
                raise NrlCatalogUpdateError('empty catalog response')
        except csv.Error as err:
            raise NrlCatalogUpdateError('invalid CSV: %s' % err)

        normalized = self._normalize_header(header)
        if normalized != CATALOG_EXPECTED_HEADER:
            raise NrlCatalogUpdateError(
                'unexpected CSV header: %r' % header
            )

        data_rows = 0
        try:
            for row in reader:
                if not row or all(not str(cell).strip() for cell in row):
                    continue
                if len(row) != len(CATALOG_EXPECTED_HEADER):
                    raise NrlCatalogUpdateError(
                        'invalid CSV data row: %r' % row
                    )
                data_rows += 1
        except csv.Error as err:
            raise NrlCatalogUpdateError('invalid CSV: %s' % err)

        return data_rows > 0

# ****************************************************************************
#
# This file is part of the yasmine editing tool.
#
# yasmine (Yet Another Station Metadata INformation Editor), a tool to
# create and edit station metadata information in FDSN stationXML format,
# is a common development of IRIS and RESIF.
# Development and addition of new features is shared and agreed between * IRIS and RESIF.
#
#
# Version 1.0 of the software was funded by SAGE, a major facility fully
# funded by the National Science Foundation (EAR-1261681-SAGE),
# development done by ISTI and led by IRIS Data Services.
# Version 2.0 of the software was funded by CNRS and development led by * RESIF.
#
# NRLv2 online support (2026): ASGSR, Alexey Emanov.
#
# This program is free software; you can redistribute it
# and/or modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version. *
# This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License (GNU-LGPL) for more details. *
# You should have received a copy of the GNU Lesser General Public
# License along with this software. If not, see
# <https://www.gnu.org/licenses/>
#
#
# 2019/10/07 : version 2.0.0 initial commit
# 2026-09-24, version 4.3.3-beta: ASGSR, Alexey Emanov
#
# ****************************************************************************/


import io
import os
import pickle
from random import random
import shutil
import tempfile
import zipfile
import logging
import requests
from obspy import read_inventory
from obspy.clients.nrl import NRL
from obspy.core.inventory.util import Equipment

from yasmine.app.helpers.base_helper import BaseHelper, _normalize_response_units
from yasmine.app.helpers.utils.utils import plot_max_frequency, response_plot_stages
from yasmine.app.utils.response_plot import format_plot_failure
from yasmine.app.helpers.nrl.nrl_catalog_update import (
    NrlCatalogUpdateError,
    NrlCatalogUpdateHelper,
)
from yasmine.app.helpers.nrl.nrl_channel_code_helper import NrlChannelCodeHelper
from yasmine.app.helpers.nrl.nrl_key_creator import NrlKeyCreator
from yasmine.app.settings import (
    MEDIA_ROOT,
    NRL_CATALOG_URL,
    NRL_HTTP_TIMEOUT,
    NRL_ROOT,
    NRL_URL,
)
from yasmine.app.utils.date import get_utcnow_naive
from yasmine.app.utils.zip_safe import UnsafeZipError, safe_extractall


NRL_MAX_UNCOMPRESSED_BYTES = 300 * 1024 * 1024 * 1024
NRL_SINGLE_ELEMENTS = ('integrated', 'soh')
NRL_ELEMENT_MISSING_TEXT = 'This response type is not in the downloaded NRL'
NO_RESPONSE_IN_RESP = 'No response in RESP file'


def response_from_resp(source):
    """First non-empty channel response in a RESP file."""
    inventory = read_inventory(source, format='RESP')
    for network in inventory.networks:
        for station in network.stations:
            for channel in station.channels:
                if channel.response:
                    return _normalize_response_units(channel.response)
    raise ValueError(NO_RESPONSE_IN_RESP)


def build_resp_element_tree(folder):
    """Breadcrumb tree of RESP files under one NRL element directory.

    Directories become branches and ``*.resp`` files become leaves. A missing
    or empty directory returns a single message node so the selector can say
    the downloaded archive does not contain this response type.
    """
    if not folder or not os.path.isdir(folder):
        return [_missing_element_node()]
    children = _walk_resp_dir(folder)
    if not children:
        return [_missing_element_node()]
    return children


def _missing_element_node():
    return {
        'text': NRL_ELEMENT_MISSING_TEXT,
        'key': '',
        'leaf': True,
    }


def _walk_resp_dir(folder):
    nodes = []
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        return nodes
    for name in names:
        if not name or name.startswith('.'):
            continue
        if name in ('.', '..') or '/' in name or '\\' in name:
            continue
        path = os.path.join(folder, name)
        if os.path.isdir(path):
            children = _walk_resp_dir(path)
            if children:
                nodes.append({
                    'text': name,
                    'key': name,
                    'leaf': False,
                    'children': children,
                })
        elif name.lower().endswith('.resp'):
            nodes.append({
                'key': name,
                'text': name[:-5],
                'leaf': True,
            })
    return nodes


class NrlArchiveUpdateError(Exception):
    """Raised when downloading or installing the NRL ZIP archive fails."""


class NrlHelper(BaseHelper):
    def __init__(
        self,
        root_folder=None,
        library_url=None,
        catalog_url=None,
        timeout=None,
        media_root=None,
        utcnow_fn=None,
        session=None,
        *_,
        **__,
    ):
        root = root_folder if root_folder is not None else NRL_ROOT
        url = library_url if library_url is not None else NRL_URL
        super().__init__(root, url, *_, **__)
        self._nrl = None
        self.logger = logging.getLogger(__name__)
        self.catalog_url = catalog_url if catalog_url is not None else NRL_CATALOG_URL
        self.timeout = timeout if timeout is not None else NRL_HTTP_TIMEOUT
        self.media_root = media_root if media_root is not None else MEDIA_ROOT
        self.utcnow_fn = utcnow_fn or get_utcnow_naive
        self.session = session or requests
        self.catalog_helper = NrlCatalogUpdateHelper(
            root_folder=self.root_folder,
            catalog_url=self.catalog_url,
            timeout=self.timeout,
            utcnow_fn=self.utcnow_fn,
            session=self.session,
            logger=self.logger,
        )

    def sync(self):
        """Check catalog updates and install full NRL ZIP only when needed."""
        try:
            if self._needs_initial_install():
                self.logger.info(
                    'NRL updates found; downloading full archive'
                )
                self._download_and_install_archive(initial=True)
                return True

            updatedsince = self.catalog_helper.get_last_successful_download_date()
            if not updatedsince:
                # Archive exists but date unknown (upgrade from older Yasmine).
                self.logger.info(
                    'NRL updates found; downloading full archive'
                )
                self._download_and_install_archive(initial=True)
                return True

            try:
                has_updates = self.catalog_helper.has_updates_since(updatedsince)
            except NrlCatalogUpdateError as err:
                self.logger.error(
                    'NRL catalog update check failed: %s', err
                )
                raise

            if not has_updates:
                self.logger.info(
                    'No NRL updates found; archive download skipped'
                )
                return True

            self.logger.info('NRL updates found; downloading full archive')
            self._download_and_install_archive(initial=False)
            return True
        except NrlCatalogUpdateError:
            return False
        except NrlArchiveUpdateError as err:
            self.logger.error(
                'NRL archive download/update failed: %s', err
            )
            return False
        except Exception as err:
            self.logger.exception(
                'NRL archive download/update failed: %s', err
            )
            return False

    def _needs_initial_install(self):
        nrl_path = os.path.join(self.content_folder, 'NRL')
        return not os.path.isdir(nrl_path)

    def _download_and_install_archive(self, initial=False):
        zip_bytes = self._download_zip()
        self.logger.info('NRL archive downloaded successfully')
        staging_content = None
        staging_keys = None
        backup_content = None
        backup_keys = None
        created_keys = []
        try:
            staging_content, staging_keys = self._prepare_staging(zip_bytes)
            backup_content, backup_keys, created_keys = self._install_from_staging(
                staging_content, staging_keys
            )
            # content staging dir was renamed into place.
            staging_content = None
            self._nrl = None
            self.logger.info('NRL archive updated successfully')
            try:
                self.catalog_helper.save_last_successful_download_date()
            except Exception as err:
                # The new library is already in place. Rolling it back because
                # the date file failed would discard a good install.
                self.logger.error(
                    'NRL archive is installed but the download date was not saved: %s',
                    err,
                )
            self._cleanup_path(backup_content)
            self._cleanup_path(backup_keys)
            backup_content = None
            backup_keys = None
        except Exception as err:
            if backup_content or backup_keys:
                self._rollback_install(backup_content, backup_keys, created_keys)
                backup_content = None
                backup_keys = None
            raise NrlArchiveUpdateError(err)
        finally:
            self._cleanup_path(staging_content)
            self._cleanup_path(staging_keys)
            self._cleanup_path(backup_content)
            self._cleanup_path(backup_keys)

    def _download_zip(self):
        try:
            response = self.session.get(
                self.library_url, timeout=self.timeout
            )
        except requests.Timeout as err:
            raise NrlArchiveUpdateError('timeout: %s' % err)
        except requests.RequestException as err:
            raise NrlArchiveUpdateError('connection error: %s' % err)

        if response.status_code != 200:
            raise NrlArchiveUpdateError(
                'HTTP %s' % response.status_code
            )

        content = response.content
        if not content:
            raise NrlArchiveUpdateError('empty ZIP response')

        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                bad = zf.testzip()
                if bad is not None:
                    raise NrlArchiveUpdateError(
                        'corrupt ZIP entry: %s' % bad
                    )
                names = zf.namelist()
        except zipfile.BadZipFile as err:
            raise NrlArchiveUpdateError('invalid ZIP: %s' % err)

        if not any(
            name == 'NRL' or name == 'NRL/' or name.startswith('NRL/')
            for name in names
        ):
            raise NrlArchiveUpdateError(
                'ZIP does not contain NRL/ directory'
            )
        return content

    def _prepare_staging(self, zip_bytes):
        os.makedirs(self.media_root, exist_ok=True)
        staging_content = tempfile.mkdtemp(
            prefix='nrl_staging_content_', dir=self.media_root
        )
        staging_keys = tempfile.mkdtemp(
            prefix='nrl_staging_keys_', dir=self.media_root
        )
        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                try:
                    safe_extractall(
                        zf,
                        staging_content,
                        max_bytes=NRL_MAX_UNCOMPRESSED_BYTES,
                    )
                except UnsafeZipError as err:
                    raise NrlArchiveUpdateError(str(err))
            nrl_path = os.path.join(staging_content, 'NRL')
            if not os.path.isdir(nrl_path):
                raise NrlArchiveUpdateError(
                    'extracted archive has no NRL/ directory'
                )
            # Validate that ObsPy can open the extracted library and build keys.
            nrl = NRL(nrl_path)
            sensors, dataloggers = NrlKeyCreator().create_keys(
                nrl.sensors, nrl.dataloggers
            )
            with open(
                os.path.join(staging_keys, self.sensor_keys_file), 'wb'
            ) as outfile:
                outfile.write(pickle.dumps(sensors))
            with open(
                os.path.join(staging_keys, self.datalogger_keys_file), 'wb'
            ) as outfile:
                outfile.write(pickle.dumps(dataloggers))
            self._write_element_key_files(nrl_path, staging_keys)
            return staging_content, staging_keys
        except NrlArchiveUpdateError:
            self._cleanup_path(staging_content)
            self._cleanup_path(staging_keys)
            raise
        except Exception as err:
            self._cleanup_path(staging_content)
            self._cleanup_path(staging_keys)
            raise NrlArchiveUpdateError(
                'cannot prepare NRL archive: %s' % err
            )

    def _install_from_staging(self, staging_content, staging_keys):
        os.makedirs(self.root_folder, exist_ok=True)
        backup_content = None
        backup_keys = None
        created_keys = []
        try:
            if os.path.exists(self.content_folder):
                backup_content = self.content_folder + '.bak'
                self._cleanup_path(backup_content)
                os.rename(self.content_folder, backup_content)
            os.rename(staging_content, self.content_folder)

            for key_name in self._library_key_files():
                dst = os.path.join(self.root_folder, key_name)
                src = os.path.join(staging_keys, key_name)
                if os.path.exists(dst):
                    if backup_keys is None:
                        backup_keys = tempfile.mkdtemp(
                            prefix='nrl_keys_bak_', dir=self.media_root
                        )
                    os.rename(dst, os.path.join(backup_keys, key_name))
                else:
                    created_keys.append(key_name)
                if os.path.exists(src):
                    os.rename(src, dst)
            return backup_content, backup_keys, created_keys
        except Exception as err:
            # Restore previous library/keys before surfacing the error.
            self._rollback_install(backup_content, backup_keys, created_keys)
            raise NrlArchiveUpdateError(
                'cannot install NRL archive: %s' % err
            )

    def _rollback_install(self, backup_content, backup_keys, created_keys=None):
        try:
            restored = set()
            if backup_content and os.path.exists(backup_content):
                self._cleanup_path(self.content_folder)
                os.rename(backup_content, self.content_folder)
            if backup_keys and os.path.isdir(backup_keys):
                for key_name in self._library_key_files():
                    src = os.path.join(backup_keys, key_name)
                    if os.path.exists(src):
                        dst = os.path.join(self.root_folder, key_name)
                        self._cleanup_path(dst)
                        os.rename(src, dst)
                        restored.add(key_name)
            for key_name in created_keys or []:
                if key_name in restored:
                    continue
                self._cleanup_path(os.path.join(self.root_folder, key_name))
        except Exception as err:
            self.logger.error(
                'NRL archive rollback failed: %s', err
            )

    @staticmethod
    def _cleanup_path(path):
        if not path:
            return
        try:
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            elif os.path.exists(path):
                os.remove(path)
        except OSError:
            pass

    def get_sensor_response_obj(self, sensor_keys):
        return self.nrl.get_sensor_response(sensor_keys)

    def get_sensor_response_str(self, sensor_keys):
        path = self._build_path(self.nrl.sensors, sensor_keys)
        return self._load_file(path[1])

    def get_sensor_equipment(self, sensor_keys):
        path = self._build_path(self.nrl.sensors, sensor_keys)
        return Equipment(manufacturer=sensor_keys[0], model=', '.join(sensor_keys[1: -1]), description=path[0])

    def get_datalogger_response_obj(self, datalogger_keys):
        return self.nrl.get_datalogger_response(datalogger_keys)

    def get_datalogger_response_str(self, datalogger_keys):
        path = self._build_path(self.nrl.dataloggers, datalogger_keys)
        return self._load_file(path[1])

    def get_datalogger_equipment(self, datalogger_keys):
        path = self._build_path(self.nrl.dataloggers, datalogger_keys)
        return Equipment(manufacturer=datalogger_keys[0], model=', '.join(datalogger_keys[1: -1]), description=path[0])

    def get_channel_response_obj(self, sensor_keys, datalogger_keys):
        sensor_resp, sensor_resp_type = self.nrl._get_response('sensors', keys=sensor_keys)
        datalogger_resp, datalogger_resp_type = self.nrl._get_response(
            'dataloggers', keys=datalogger_keys
        )
        _normalize_response_units(sensor_resp)
        _normalize_response_units(datalogger_resp)
        combined = self.nrl._combine_sensor_datalogger(
            sensor_resp, datalogger_resp, sensor_resp_type, datalogger_resp_type
        )
        # Always recompute stage-0 after the cascade. A complete-looking unit
        # pair can still carry the pre-cascade sensitivity.
        combined = _normalize_response_units(combined)
        try:
            self._recalculate_sensitivity(combined)
        except Exception as err:
            self.logger.error('NRL sensitivity was not recalculated: %s', err)
        return combined

    def _recalculate_sensitivity(self, response):
        from yasmine.app.utils.response_sensitivity import recalculate_response_sensitivity
        recalculate_response_sensitivity(response, allow_zero_gain_reset=True)

    def _library_key_files(self):
        return (
            self.sensor_keys_file,
            self.datalogger_keys_file,
            'integrated.json',
            'soh.json',
        )

    def _write_element_key_files(self, nrl_path, dest_dir):
        for element in NRL_SINGLE_ELEMENTS:
            tree = build_resp_element_tree(os.path.join(nrl_path, element))
            with open(os.path.join(dest_dir, '%s.json' % element), 'wb') as outfile:
                outfile.write(pickle.dumps(tree))

    def get_element_keys(self, element):
        """Manufacturer tree for integrated or SOH responses in the offline archive."""
        self._require_single_element(element)
        key_file = '%s.json' % element
        path = os.path.join(self.root_folder, key_file)
        if os.path.exists(path):
            return self._load_keys_file(key_file)
        return build_resp_element_tree(self._element_dir(element))

    def get_element_response_str(self, element, keys):
        with open(self._element_resp_path(element, keys), 'r') as handle:
            return handle.read()

    def get_element_response_obj(self, element, keys):
        return response_from_resp(self._element_resp_path(element, keys))

    def get_element_equipment(self, element, keys):
        self._require_single_element(element)
        safe_keys = self._safe_key_parts(keys)
        manufacturer = safe_keys[0] if safe_keys else ''
        leaf = safe_keys[-1] if safe_keys else ''
        if leaf.lower().endswith('.resp'):
            leaf = leaf[:-5]
        return Equipment(
            manufacturer=manufacturer,
            model=leaf,
            description='/'.join(safe_keys),
        )

    def get_element_response_and_plot(self, element, keys, min_fq, max_fq,
                                      start_stage=None, end_stage=None):
        try:
            response_str = self.get_element_response_str(element, keys)
        except Exception as err:
            return {'success': False, 'message': 'Cannot build channel response.<br> %s' % err}
        resp = None
        try:
            resp = self.get_element_response_obj(element, keys)
            min_fq = float(min_fq) if min_fq else None
            max_fq = float(max_fq) if max_fq else None
            label = [element] + list(self._safe_key_parts(keys))
            plot_file_name = self.generate_channel_response_plot(
                resp, label, [], min_fq, max_fq,
                start_stage=start_stage, end_stage=end_stage
            )
            plot_url = '/api/channel/response/plots/plots/%s?_dc=%s' % (plot_file_name, random())
            csv_file_name = self.generate_channel_response_csv(
                resp, label, [], min_fq, max_fq,
                start_stage=start_stage, end_stage=end_stage
            )
            csv_url = '/api/channel/response/plots/plots/%s?_dc=%s' % (csv_file_name, random())
        except ValueError as err:
            return {'success': False, 'message': str(err)}
        except Exception as err:
            self.logger.exception('Cannot generate plot')
            return {
                'success': True,
                'text': response_str,
                'message': format_plot_failure(err, resp),
                'plot_failed': True,
            }
        return {
            'success': True,
            'text': response_str,
            'plot_url': plot_url,
            'csv_url': csv_url,
            'max_frequency': plot_max_frequency(resp, max_fq, min_fq),
            'stages': response_plot_stages(resp),
        }

    def _element_dir(self, element):
        return os.path.join(self.content_folder, 'NRL', element)

    def _element_resp_path(self, element, keys):
        self._require_single_element(element)
        root = self._element_dir(element)
        if not os.path.isdir(root):
            raise ValueError('This response type is not in the downloaded NRL')
        parts = self._safe_key_parts(keys)
        if not parts:
            raise ValueError('RESP file not found')
        candidate = os.path.realpath(os.path.join(root, *parts))
        root_real = os.path.realpath(root)
        if candidate != root_real and not candidate.startswith(root_real + os.sep):
            raise ValueError('invalid path')
        if not candidate.lower().endswith('.resp') and os.path.isfile(candidate + '.resp'):
            candidate = candidate + '.resp'
        if not os.path.isfile(candidate):
            raise ValueError('RESP file not found')
        return candidate

    @staticmethod
    def _require_single_element(element):
        if element not in NRL_SINGLE_ELEMENTS:
            raise ValueError('unsupported element')

    @staticmethod
    def _safe_key_parts(keys):
        if isinstance(keys, str):
            keys = [keys]
        parts = []
        for key in keys or []:
            name = str(key or '').strip()
            if not name or name in ('.', '..') or '/' in name or '\\' in name:
                raise ValueError('invalid key')
            parts.append(name)
        return parts

    def guess_channel_code(self, sensors_keys, datalogger_keys):
        channel_code_helper = NrlChannelCodeHelper(self.nrl.sensors, self.nrl.dataloggers)
        path = self._build_path(self.nrl.dataloggers, datalogger_keys)
        return channel_code_helper.guess_code(sensors_keys, datalogger_keys, path[0])

    def _load_library(self):
        # Kept for BaseHelper compatibility; NRL sync uses _download_and_install_archive.
        self._download_and_install_archive(initial=self._needs_initial_install())

    def _create_keys_files(self):
        self.logger.info('Creating an NRL key files')
        sensors, dataloggers = NrlKeyCreator().create_keys(self.nrl.sensors, self.nrl.dataloggers)
        self._save_keys_files(sensors, dataloggers)
        self._write_element_key_files(
            os.path.join(self.content_folder, 'NRL'),
            self.root_folder,
        )
        self.logger.info('NRL key files have been created')

    @staticmethod
    def _build_path(nrl_elements, keys):
        element = nrl_elements
        for key in keys:
            element = element[key]
        return element

    @staticmethod
    def _load_file(path):
        with open(path, 'r') as f:
            return f.read()

    @property
    def nrl(self):
        if self._nrl is None:
            self._nrl = NRL(os.path.join(self.content_folder, 'NRL'))
        return self._nrl

    @nrl.setter
    def nrl(self, value):
        self._nrl = value

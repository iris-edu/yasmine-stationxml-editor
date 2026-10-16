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
# 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
#
# ****************************************************************************/


import datetime
import glob
import json
import os
import shutil
import tempfile
from io import BytesIO
from urllib.request import urlopen, Request
from zipfile import ZipFile
import logging
import yaml

from yasmine.app.settings import TMP_ROOT
from yasmine.app.utils.url_guard import UrlGuardError, validate_url
from yasmine.app.utils.zip_safe import safe_extract_flat, safe_extractall

DOWNLOAD_TIMEOUT = 30
DOWNLOAD_MAX_BYTES = 50 * 1024 * 1024


def _json_default(value):
    # PyYAML SafeLoader turns unquoted dates (AROL start_time/end_time) into
    # datetime objects. Serialize them before writing so a failed dump cannot
    # leave a truncated JSON file.
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()
    raise TypeError('Object of type %s is not JSON serializable' % type(value).__name__)


class FileConvertorService:
    def __init__(self, flattern=False, is_full_loader=False, *_, **__):
        super(FileConvertorService, self).__init__(*_, **__)
        self.flattern = flattern
        self.is_full_loader = is_full_loader
        self.logger = logging.getLogger(__name__)

    def convert_from_folder(self, folder):
        def rename_extensions(key, value):
            if '$ref' in key:
                value = value.replace('.yaml', '.json').replace('#filter', '')
            return value

        temp_folder = tempfile.mkdtemp(dir=TMP_ROOT)
        files = [f for f in glob.glob(folder + "/**/*.yaml", recursive=True)]
        for file in files:
            file_out = os.path.splitext(os.path.basename(file))[0] + ".json"
            if not self.flattern:
                file_path = os.path.relpath(os.path.dirname(file), folder)
                file_abs_path = os.path.join(temp_folder, file_path)
                file_out = os.path.join(file_path, file_out)
                os.makedirs(file_abs_path, exist_ok=True)
            with open(file, 'rb') as fl:
                data_loaded = yaml.load(fl, Loader=yaml.SafeLoader)
                self._traverse(data_loaded, rename_extensions)
                out_path = os.path.join(temp_folder, file_out)
                try:
                    payload = json.dumps(data_loaded, default=_json_default)
                except (TypeError, ValueError) as error:
                    self.logger.error(f'cannot convert: "{file}": {error}')
                    continue
                with open(out_path, 'wt') as fo:
                    fo.write(payload)
        return temp_folder

    def convert_from_zip(self, zip_file):
        temp_unzip_folder = tempfile.mkdtemp(dir=TMP_ROOT)
        try:
            if self.flattern:
                safe_extract_flat(zip_file, temp_unzip_folder)
            else:
                safe_extractall(zip_file, temp_unzip_folder)
            return self.convert_from_folder(temp_unzip_folder)
        finally:
            shutil.rmtree(temp_unzip_folder, ignore_errors=True)

    def convert_from_url(self, url):
        try:
            validate_url(url)
        except UrlGuardError as err:
            raise ValueError(str(err))
        request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=DOWNLOAD_TIMEOUT) as zip_response:
            data = zip_response.read(DOWNLOAD_MAX_BYTES + 1)
            if len(data) > DOWNLOAD_MAX_BYTES:
                raise ValueError('Download exceeds size limit')
            with ZipFile(BytesIO(data)) as zip_file:
                return self.convert_from_zip(zip_file)

    def _traverse(self, data, callback):
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, dict) or isinstance(v, list) or isinstance(v, tuple):
                    self._traverse(v, callback)
                else:
                    data[k] = callback(k, v)
        elif isinstance(data, list) or isinstance(data, tuple):
            for item in data:
                self._traverse(item, callback)

        return data

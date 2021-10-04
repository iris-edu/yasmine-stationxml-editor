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
#
# ****************************************************************************/


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
                data_loaded = yaml.load(fl, Loader=yaml.FullLoader if self.is_full_loader else yaml.BaseLoader)
                self._traverse(data_loaded, rename_extensions)
                with open(os.path.join(temp_folder, file_out), 'wt') as fo:
                    try:
                        json.dump(data_loaded, fo)
                    except Exception as error:
                        self.logger.error(f'cannot convert: "{file}": {error}')
        return temp_folder

    def convert_from_zip(self, zip_file):
        temp_unzip_folder = tempfile.mkdtemp(dir=TMP_ROOT)
        if self.flattern:
            for member in zip_file.namelist():
                filename = os.path.basename(member)
                if not filename:
                    continue

                target = open(os.path.join(temp_unzip_folder, filename), "wb")
                source = zip_file.open(member)
                with source, target:
                    shutil.copyfileobj(source, target)
        else:
            zip_file.extractall(temp_unzip_folder)
        return self.convert_from_folder(temp_unzip_folder)

    def convert_from_url(self, url):
        request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request) as zip_response:
            with ZipFile(BytesIO(zip_response.read())) as zip_file:
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

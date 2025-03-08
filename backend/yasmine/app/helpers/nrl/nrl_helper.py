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


import io
import os
import shutil
import tempfile
import zipfile
import logging
import requests
from obspy.clients.nrl import NRL
from obspy.core.inventory.util import Equipment

from yasmine.app.helpers.base_helper import BaseHelper
from yasmine.app.helpers.nrl.nrl_channel_code_helper import NrlChannelCodeHelper
from yasmine.app.helpers.nrl.nrl_key_creator import NrlKeyCreator
from yasmine.app.settings import NRL_ROOT, NRL_URL, MEDIA_ROOT


class NrlHelper(BaseHelper):
    def __init__(self, *_, **__):
        super().__init__(NRL_ROOT, NRL_URL, *_, **__)
        self._nrl = None
        self.logger = logging.getLogger(__name__)

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
        return self.nrl.get_response(sensor_keys=sensor_keys, datalogger_keys=datalogger_keys)

    def guess_channel_code(self, sensors_keys, datalogger_keys):
        channel_code_helper = NrlChannelCodeHelper(self.nrl.sensors, self.nrl.dataloggers)
        path = self._build_path(self.nrl.dataloggers, datalogger_keys)
        return channel_code_helper.guess_code(sensors_keys, datalogger_keys, path[0])

    def _load_library(self):
        self.logger.info(f'Loading NRL from {NRL_URL}')
        r = requests.get(NRL_URL)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        tmp_dir = tempfile.mkdtemp(dir=MEDIA_ROOT)
        self.logger.info(f'Unzipping NRL')
        z.extractall(tmp_dir)
        shutil.rmtree(self.content_folder, True)
        os.rename(tmp_dir, self.content_folder)
        self.logger.info(f'NRL has been unzipped')

    def _create_keys_files(self):
        self.logger.info(f'Creating an NRL key files')
        sensors, dataloggers = NrlKeyCreator().create_keys(self.nrl.sensors, self.nrl.dataloggers)
        self._save_keys_files(sensors, dataloggers)
        self.logger.info(f'NRL key files have been created')

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
            self._nrl = NRL(os.path.join(self.content_folder,'NRL'))
        return self._nrl

    @nrl.setter
    def nrl(self, value):
        self._nrl = value

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


import copy
import os
import shutil
import logging
from pathlib import Path

import jsonref
import yaml
from obspy.core.inventory.util import Equipment

from yasmine.app.helpers.base_helper import BaseHelper
from yasmine.app.helpers.ial.ial_channel_code_helper import IalChannelCodeHelper
from yasmine.app.helpers.ial.ial_channel_response_builder import IalChannelResponseBuilder
from yasmine.app.helpers.ial.ial_key_creator import IalKeyCreator
from yasmine.app.services.file_convertor_service import FileConvertorService
from yasmine.app.settings import IAL_URL, IAL_ROOT, IAL_FOLDER


class IalHelper(BaseHelper):
    def __init__(self, *_, **__):
        super().__init__(IAL_ROOT, IAL_URL, *_, **__)
        self.sensor_folder = 'Sensors'
        self.datalogger_folder = 'Dataloggers'
        self.content_data_folder = os.path.join(self.content_folder, IAL_FOLDER, 'objects')
        self.logger = logging.getLogger(__name__)

    def get_sensor_response_obj(self, sensor_keys):
        responses = []
        for key in sensor_keys:
            path = self._build_path(key, self.sensor_folder)
            responses.append(self._load_response(path))
        return responses

    def get_sensor_response_str(self, sensor_keys):
        return yaml.dump(self.get_sensor_response_obj(sensor_keys))

    def get_sensor_equipment(self, sensor_keys):
        return self.string_equipment_helper(sensor_keys)

    def get_datalogger_response_obj(self, datalogger_keys):
        responses = []
        for key in datalogger_keys:
            path = self._build_path(key, self.datalogger_folder)
            responses.append(self._load_response(path))
        return responses

    def get_datalogger_response_str(self, datalogger_keys):
        return yaml.dump(self.get_datalogger_response_obj(datalogger_keys))

    def get_datalogger_equipment(self, datalogger_keys):
        return self.string_equipment_helper(datalogger_keys)

    def string_equipment_helper(self, keys):
        keys_string = keys[0]
        manufacturer = keys_string.split("/")[0].capitalize()
        model = keys_string.split("/")[1].split('.')[0]
        return Equipment(manufacturer=manufacturer, model=model, description=manufacturer + ", " + model)

    def get_channel_response_obj(self, sensor_keys, datalogger_keys):
        sensor = self.get_sensor_response_obj(sensor_keys)
        datalogger = self.get_datalogger_response_obj(datalogger_keys)
        return IalChannelResponseBuilder().build(sensor, datalogger)

    def guess_channel_code(self, sensors_keys, datalogger_keys):
        return IalChannelCodeHelper().guess_code(sensors_keys, datalogger_keys)

    def _load_library(self):
        self.logger.info(f'Loading and unzipping AROL from {IAL_URL}')
        temp_folder = FileConvertorService().convert_from_url(IAL_URL)
        shutil.rmtree(self.content_folder, True)
        shutil.copytree(temp_folder, self.content_folder)
        shutil.rmtree(temp_folder)
        self.logger.info(f'AROL has been unzipped')

    def _load_response(self, file):
        if not os.path.exists(file):
            return {'error': 'can not find file', 'file': file}
        with open(file, 'rb') as f:
            data_loaded = jsonref.load(f, base_uri=Path(file).as_uri())
            return self._flatten_extras(data_loaded)

    @staticmethod
    def _flatten_extras(data_loaded):
        """
        flatten out the response stages by shoving all the 'extras' into a single stage['extras'] list of dicts
        and same for the 'notes'...
        Move stage['filter']['filter'] up to stage['filter']

        Note that if the input stage has no 'extras' ('notes') the output stage will have an empty list.
        """

        data_copy = copy.deepcopy(data_loaded)

        for stage in data_copy['response']['stages']:
            extras = []
            notes = []
            if 'extras' in stage:
                extras.append(stage['extras'])
                del stage['extras']
            if 'notes' in stage:
                notes.append(stage['notes'])
                del stage['notes']
            stage['extras'] = extras
            stage['notes'] = notes

            if 'filter' in stage:
                if 'extras' in stage['filter']:
                    extras.append(stage['filter']['extras'])
                    del stage['filter']['extras']
                if 'notes' in stage['filter']:
                    notes.append(stage['filter']['notes'])
                    del stage['filter']['notes']
                if 'filter' in stage['filter']:
                    stage['filter'] = stage['filter']['filter']

        return data_copy

    def _build_path(self, file_path, folder):
        return os.path.join(self.content_data_folder, folder, file_path.replace('yaml', 'json'))

    def _create_keys_files(self):
        sensors, dataloggers = IalKeyCreator().create_keys(self.content_data_folder)
        self._save_keys_files(sensors, dataloggers)

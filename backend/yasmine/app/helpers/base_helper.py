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


import os
import pickle
from random import random
from yasmine.app.helpers.etag_helper import EtagHelper
from yasmine.app.helpers.utils.utils import ChannelUtils
from yasmine.app.settings import MEDIA_ROOT
from yasmine.app.utils.response_plot import polynomial_or_polezero_response


class BaseHelper:
    def __init__(self, root_folder, library_url, *_, **__):
        self.root_folder = root_folder
        self.library_url = library_url
        self.etag_helper = EtagHelper(root_folder, library_url)
        self.sensor_keys_file = 'sensors.json'
        self.datalogger_keys_file = 'dataloggers.json'
        self.content_folder = os.path.join(root_folder, 'content')
        self.plot_folder = os.path.join(MEDIA_ROOT, 'plots')
        os.makedirs(self.content_folder, exist_ok=True)
        os.makedirs(self.plot_folder, exist_ok=True)

    def sync(self):
        if not self.etag_helper.is_new_etag_available():
            return
        self._load_library()
        self._create_keys_files()
        self.etag_helper.save_etag()

    def get_channel_response_obj(self, sensor_keys, datalogger_keys):
        raise NotImplementedError('Subclass needs to implement this method')

    def _load_library(self):
        raise NotImplementedError('Subclass needs to implement this method')

    def _create_keys_files(self):
        raise NotImplementedError('Subclass needs to implement this method')

    def get_sensors_keys(self):
        return self._load_keys_file(self.sensor_keys_file)

    def get_dataloggers_keys(self):
        return self._load_keys_file(self.datalogger_keys_file)

    def get_channel_response_str(self, sensor_keys, datalogger_keys):
        response = self.get_channel_response_obj(sensor_keys, datalogger_keys)
        return polynomial_or_polezero_response(response)

    def generate_channel_response_plot(self, response, sensors_keys, datalogger_keys, min_frequency, max_frequency):
        file_name = ''.join(sensors_keys) + '_' + ''.join(datalogger_keys)
        return ChannelUtils.create_response_plot(response, self.plot_folder, file_name, min_frequency, max_frequency)

    def generate_channel_response_csv(self, response, sensors_keys, datalogger_keys, min_frequency, max_frequency):
        file_name = ''.join(sensors_keys) + '_' + ''.join(datalogger_keys)
        return ChannelUtils.create_response_csv(response, self.plot_folder, file_name, min_frequency, max_frequency)

    def get_sensor_response_and_plot(self, sensor_keys, datalogger_keys, min_fq, max_fq):
        try:
            response_str = self.get_channel_response_str(sensor_keys, datalogger_keys)
        except Exception as err:
            return {'success': False, 'message': f'Cannot build channel response.<br> {err}'}
        try:
            resp = self.get_channel_response_obj(sensor_keys, datalogger_keys)
            min_fq = float(min_fq) if min_fq else None
            max_fq = float(max_fq) if max_fq else None
            plot_file_name = self.generate_channel_response_plot(resp, sensor_keys, datalogger_keys, min_fq, max_fq)
            plot_url = f'/api/channel/response/plots/plots/{plot_file_name}?_dc={random()}'
            csv_file_name = self.generate_channel_response_csv(resp, sensor_keys, datalogger_keys, min_fq, max_fq)
            csv_url = f'/api/channel/response/plots/plots/{csv_file_name}?_dc={random()}'
        except Exception as err:
            return {'success': True, 'text': response_str, 'message': f'Cannot generate plot.<br> {err}'}

        return {'success': True, 'text': response_str, 'plot_url': plot_url, 'csv_url': csv_url}

    def _save_keys_files(self, sensors, dataloggers):
        with open(os.path.join(self.root_folder, self.sensor_keys_file), 'wb') as outfile:
            outfile.write(pickle.dumps(sensors))
        with open(os.path.join(self.root_folder, self.datalogger_keys_file), 'wb') as outfile:
            outfile.write(pickle.dumps(dataloggers))

    def _load_keys_file(self, key_file_name):
        file = os.path.join(self.root_folder, key_file_name)
        if not os.path.exists(file):
            return [{'text': 'Library is not loaded yet...'}]
        with open(file, 'rb') as outfile:
            return pickle.loads(outfile.read())

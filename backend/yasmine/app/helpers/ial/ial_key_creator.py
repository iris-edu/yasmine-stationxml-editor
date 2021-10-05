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
from pathlib import Path

import jsonref

from yasmine.app.services.file_validator_service import FileValidatorService
from yasmine.app.settings import RESOURCES_SCHEMA_AROL


class IalKeyCreator:

    def create_keys(self, folder):
        sensors = self._create(os.path.join(folder, 'Sensors'))
        dataloggers = self._create(os.path.join(folder, 'Dataloggers'))
        return sensors, dataloggers

    def _create(self, folder):
        key_files = self._find_all_key_files(folder)
        errors = FileValidatorService().validate(key_files, os.path.join(RESOURCES_SCHEMA_AROL, 'key.schema.json'))
        result = {'filters': [], 'responses': []}

        if len(errors) > 0:
            return result

        for file in key_files:
            with open(file, 'rb') as fl:
                data_loaded = jsonref.load(fl, base_uri=Path(os.path.dirname(file)).as_uri())
                req_key = "mandatory_filters"
                for resp_filter in data_loaded.get('filters'):
                    if not next((sub for sub in result.get('filters') if sub['code'] == resp_filter['code']), None):
                        resp_filter['required'] = req_key in data_loaded and resp_filter['code'] in data_loaded[req_key]
                        result.get('filters').append(resp_filter)

                all_filter_codes = list(map(lambda x: x['code'], data_loaded.get('filters')))
                for response_option in data_loaded.get('responses'):
                    applicable_filters = response_option.get('applicable_filters')
                    response_filter_codes = list(applicable_filters.keys())
                    missed_filter_codes = list(set(all_filter_codes) - set(response_filter_codes))
                    for missed_filter_code in missed_filter_codes:
                        applicable_filters[missed_filter_code] = None
                    result.get('responses').append(response_option)
        return result

    @staticmethod
    def _find_all_key_files(folder):
        result = []
        for x in os.listdir(folder):
            file = os.path.join(folder, f'{x}/{x}.json')
            if os.path.isfile(file):
                result.append(file)
        return result

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
import logging
import os
import shutil
from pathlib import Path

import jsonref

from yasmine.app.enums.xml_node import XmlNodeEnum, XmlNodeAttrEnum
from yasmine.app.exceptions.exceptions import BusinessException
from yasmine.app.lookup.lookup_objects import OperatorLookup
from yasmine.app.models import XmlNodeAttrValModel, XmlNodeAttrModel
from yasmine.app.services.file_convertor_service import FileConvertorService
from yasmine.app.services.file_validator_service import FileValidatorService
from yasmine.app.settings import RESOURCES_SCHEMA_GATITO
from yasmine.app.utils.facade import HandlerMixin


class UserLibraryService(HandlerMixin):
    def __init__(self, *_, **__):
        super(UserLibraryService, self).__init__(*_, **__)
        self.logger = logging.getLogger(__name__)

    def import_from_url(self, url):
        new_folder = FileConvertorService(True, True).convert_from_url(url)
        self._parse_library(new_folder)
        shutil.rmtree(new_folder)

    def import_from_zip(self, zip_file):
        new_folder = FileConvertorService(True, True).convert_from_zip(zip_file)
        self._parse_library(new_folder)
        shutil.rmtree(new_folder)

    def import_from_folder(self, folder):
        new_folder = FileConvertorService(True, True).convert_from_folder(folder)
        self._parse_library(new_folder)
        shutil.rmtree(new_folder)

    def _parse_library(self, folder):
        self._validate_files(folder)

        with self.db.begin():
            self.db.query(XmlNodeAttrValModel)\
                .filter(XmlNodeAttrValModel.node_inst_id.is_(None))\
                .delete()
            attributes = self.db.query(XmlNodeAttrModel).all()
            self.db.add_all(self._parse_common_library(attributes, folder))
            self.db.add_all(self._parse_station_library(attributes, folder))
            self.db.add_all(self._parse_channel_library(attributes, folder))

    def _validate_files(self, folder):
        files = [p for p in Path(folder).iterdir() if p.is_file()]
        all_errors = []
        for file in files:
            file_name = Path(file).stem
            schema = os.path.join(RESOURCES_SCHEMA_GATITO, f'{file_name}.schema.json')
            errors = FileValidatorService(self).validate([file], schema)
            all_errors.extend(errors)
        if len(all_errors) > 0:
            raise BusinessException('Gatito library is not valid, see log.')

    def _parse_common_library(self, attributes, folder):
        result = []
        data_loaded, attr_id = self._load_file(folder, 'identifier.json', attributes, XmlNodeAttrEnum.IDENTIFIERS)
        for item in data_loaded:
            value_obj = {'value': f'{item.get("type")}:{item.get("Identifier")}', 'description': item.get('Help')}
            result.append(XmlNodeAttrValModel(node_id=XmlNodeEnum.NETWORK, attr_id=attr_id, value_obj=value_obj.copy()))
            result.append(XmlNodeAttrValModel(node_id=XmlNodeEnum.STATION, attr_id=attr_id, value_obj=value_obj.copy()))
            result.append(XmlNodeAttrValModel(node_id=XmlNodeEnum.CHANNEL, attr_id=attr_id, value_obj=value_obj.copy()))
        return result

    def _parse_station_library(self, attributes, folder):
        result = []
        node_id = XmlNodeEnum.STATION

        data_loaded, attr_id = self._load_file(folder, 'vault.json', attributes, XmlNodeAttrEnum.VAULT)
        for item in data_loaded:
            value_obj = {'value': item.get('Vault'), 'description': item.get('Help')}
            result.append(XmlNodeAttrValModel(node_id=node_id, attr_id=attr_id, value_obj=value_obj))

        data_loaded, attr_id = self._load_file(folder, 'geology.json', attributes, XmlNodeAttrEnum.GEOLOGY)
        for item in data_loaded:
            value_obj = {'value': item.get('Geology'), 'description': item.get('Help')}
            result.append(XmlNodeAttrValModel(node_id=node_id, attr_id=attr_id, value_obj=value_obj))

        data_loaded, attr_id = self._load_file(folder, 'operator.json', attributes, XmlNodeAttrEnum.OPERATORS)
        for item in data_loaded:
            item = OperatorLookup().create(item)
            result.append(XmlNodeAttrValModel(node_id=node_id, attr_id=attr_id, value_obj=item))

        data_loaded, attr_id = self._load_file(folder, 'station_comment.json', attributes, XmlNodeAttrEnum.COMMENTS)
        for item in data_loaded:
            comment = item.get('Comment')
            if comment:
                value_obj = {'value': comment.get('Value'), 'description': comment.get('subject')}
                result.append(XmlNodeAttrValModel(node_id=node_id, attr_id=attr_id, value_obj=value_obj))

        data_loaded, attr_id = self._load_file(folder, 'site.json', attributes, XmlNodeAttrEnum.SITE)
        for item in data_loaded:
            result.append(XmlNodeAttrValModel(node_id=node_id, attr_id=attr_id, value_obj=item.get('Site')))

        return result

    def _parse_channel_library(self, attributes, folder):
        result = []
        node_id = XmlNodeEnum.CHANNEL

        data_loaded, attr_id = self._load_file(folder, 'channel_comment.json', attributes, XmlNodeAttrEnum.COMMENTS)
        for item in data_loaded:
            comment = item.get('Comment')
            if comment:
                value_obj = {'value': comment.get('Value'), 'description': comment.get('subject')}
                result.append(XmlNodeAttrValModel(node_id=node_id, attr_id=attr_id, value_obj=value_obj))

        data_loaded, attr_id = self._load_file(folder, 'units.json', attributes, XmlNodeAttrEnum.CALIBRATION_UNITS)
        for item in data_loaded:
            value_obj = {'value': item.get('Name'), 'description': item.get('Description')}
            result.append(XmlNodeAttrValModel(node_id=node_id, attr_id=attr_id, value_obj=value_obj))

        data_loaded, attr_id = self._load_file(folder, 'units.json', attributes, XmlNodeAttrEnum.CALIBRATION_UNITS_DESCRIPTION)
        for item in data_loaded:
            value_obj = {'value': item.get('Description'), 'description': item.get('Name')}
            result.append(XmlNodeAttrValModel(node_id=node_id, attr_id=attr_id, value_obj=value_obj))

        return result

    @staticmethod
    def _load_file(folder, file_name, attributes, att_name):
        path = os.path.join(folder, file_name)
        if not os.path.isfile(path):
            return [], None
        with open(path, 'rb') as f:
            data_loaded = jsonref.load(f, base_uri=Path(folder).as_uri())
            attr_id = next((x for x in attributes if x.name == att_name), None).id
            return data_loaded, attr_id

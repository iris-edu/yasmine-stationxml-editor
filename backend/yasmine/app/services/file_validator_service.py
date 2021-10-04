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
# ****************************************************************************/


import os
import logging
from pathlib import Path

import jsonref
import jsonschema


class FileValidatorService:
    def __init__(self, *_, **__):
        self.logger = logging.getLogger(__name__)

    def validate(self, files, schema_file_path):
        errors = []
        schema = self._read_schema(schema_file_path)
        for file in files:
            with open(file, 'r') as fl:
                instance = jsonref.load(fl, base_uri=Path(os.path.dirname(file)).as_uri())
                valid_schema = jsonschema.Draft7Validator(schema)
                for error in valid_schema.iter_errors(instance):
                    error_element = "".join(f"[{err}]" for err in error.path)
                    self.logger.error(f"{file} has invalid file structure: {error_element} -> {error.message}")
                    errors.append(f"{error_element}: {error.message}")
        return errors

    @staticmethod
    def _read_schema(schema_file_path):
        file = Path(schema_file_path)
        if not file.exists():
            raise Exception(f'Cannot find "{file.name}" schema file for validation')
        with open(schema_file_path, 'r') as f:
            base_uri = Path(os.path.dirname(schema_file_path)).as_uri()
            schema = jsonref.loads(f.read(), base_uri=base_uri, jsonschema=True)
        return schema

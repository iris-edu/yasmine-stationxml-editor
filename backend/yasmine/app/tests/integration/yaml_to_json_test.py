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
import unittest
from zipfile import ZipFile

import jsonref

from yasmine.app.services.file_convertor_service import FileConvertorService


class ResifIoTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ResifIoTest, self).__init__(*args, **kwargs)

    def test_convert_from_folder(self):
        folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data/gatito/gatito-master/')
        new_folder = FileConvertorService(True).convert_from_folder(folder)
        self._check_result(new_folder)

    def test_convert_from_zip(self):
        file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data/gatito/gatito-master.zip')
        with ZipFile(file, 'r') as zip_file:
            new_folder = FileConvertorService(True).convert_from_zip(zip_file)
            self._check_result(new_folder)

    @unittest.skip
    def test_convert_from_url(self):
        url = "https://gricad-gitlab.univ-grenoble-alpes.fr/OSUG/RESIF/ResifYAMLfiles/-/archive/patch-1/" \
              "ResifYAMLfiles-patch-1.zip?path=yasmine-library"
        new_folder = FileConvertorService(True).convert_from_url(url)
        self._check_result(new_folder)

    def _check_result(self, folder):
        vault_file = f'{folder}/vault.json'
        self.assertTrue(os.path.isfile(vault_file))

        with open(vault_file) as f:
            json_content = jsonref.load(f, base_uri='file://{}/'.format(folder))
            self.assertEqual(22, len(json_content))


if __name__ == "__main__":
    unittest.main()

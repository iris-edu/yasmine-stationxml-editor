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

import requests


class EtagHelper:
    def __init__(self, folder, url):
        os.makedirs(folder, exist_ok=True)
        self.url = url
        self.etag_file = os.path.join(folder, 'etag.txt')
        self.etag_new = None

    def is_new_etag_available(self):
        self._init_etag_file()

        self.etag_new = self._load_etag()
        with open(self.etag_file, 'rt') as f:
            return self.etag_new != f.read()

    def save_etag(self):
        if self.etag_new:
            with open(self.etag_file, 'wt') as f:
                f.write(self.etag_new)

    def _init_etag_file(self):
        open(self.etag_file, 'a').close()

    def _load_etag(self):
        h = requests.head(self.url, allow_redirects=True)
        header = h.headers
        return header.get('etag')

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
# 2026-09-24, version 4.3.3-beta: ASGSR, Alexey Emanov
#
# ****************************************************************************/


import io
import os

import tornado.gen

from yasmine.app.handlers.base import ExtJsHandler, AsyncThreadMixin, BaseHandler
from yasmine.app.models import XmlModel
from yasmine.app.utils.imp_exp import ImportStationXml, ExportStationXml
from yasmine.app.utils.stationxml_migration import build_import_migration_report


class XmlGridHandler(ExtJsHandler):
    model = XmlModel
    exclude_fields = ['extension_sidecar']


class XmlImpExpHandler(AsyncThreadMixin, BaseHandler):
    def async_post(self, *_, **__):
        files = self.request.files.get('xml-path')
        if not files:
            return {'success': False, 'message': 'xml-path file is required'}
        body = files[0]['body']
        filename = files[0]['filename']
        name = self.get_argument('name') or os.path.splitext(filename)[0]
        migration = build_import_migration_report(body)
        try:
            ImportStationXml(name, io.BytesIO(body), self).run()
        except ValueError as error:
            return {'success': False, 'message': str(error)}
        return {'success': True, 'migration': migration}

    def _export(self, db_id):
        return ExportStationXml(db_id, self).run()

    @tornado.gen.coroutine
    def get(self, db_id, *_, **__):
        file_name, file_data = yield self.async_call(self._export, db_id)
        self.write_file_data(file_name, file_data.getvalue())

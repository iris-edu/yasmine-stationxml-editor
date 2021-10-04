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
from urllib.error import URLError
from zipfile import BadZipFile, ZipFile

from yasmine.app.exceptions.exceptions import BusinessException
from yasmine.app.handlers.base import AsyncThreadMixin, BaseHandler
from yasmine.app.models import XmlNodeAttrValModel
from yasmine.app.services.user_library_service import UserLibraryService


class HelperHandler(AsyncThreadMixin, BaseHandler):
    def async_get(self, node_id, attr_id, *_, **__):
        db_result = self.db.query(XmlNodeAttrValModel) \
            .filter(XmlNodeAttrValModel.node_id == node_id) \
            .filter(XmlNodeAttrValModel.attr_id == attr_id) \
            .all()

        result = []
        for db_item in db_result:
            result.append(db_item.value_obj)

        return result


class ImportUrlUserLibraryHandler(AsyncThreadMixin, BaseHandler):
    def async_post(self, *_, **__):
        params = self.request_params
        try:
            UserLibraryService(self).import_from_url(params['url'])
        except BusinessException as err:
            return {'success': False, 'message': str(err)}
        except URLError as err:
            return {'success': False, 'message': err.reason}
        except BadZipFile as err:
            return {'success': False, 'message': f"{err}"}
        except FileNotFoundError as err:
            return {'success': False, 'message': f"{err.strerror}: {os.path.basename(err.filename)}"}

        return {'success': True, 'message': ''}


class ImportZipUserLibraryHandler(AsyncThreadMixin, BaseHandler):
    def async_post(self, *_, **__):
        body = self.request.files['zip-path'][0]['body']
        try:
            with ZipFile(io.BytesIO(body)) as zip_file:
                UserLibraryService(self).import_from_zip(zip_file)
        except BusinessException as err:
            return {'success': False, 'message': str(err)}
        except URLError as err:
            return {'success': False, 'message': err.reason}
        except BadZipFile as err:
            return {'success': False, 'message': f"{err}"}
        except FileNotFoundError as err:
            return {'success': False, 'message': f"{err.strerror}: {os.path.basename(err.filename)}"}

        return {'success': True, 'message': ''}

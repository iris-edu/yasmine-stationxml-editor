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

from yasmine.app.models import XmlModel
from yasmine.app.settings import TMP_ROOT
from yasmine.app.utils.facade import HandlerMixin
from datetime import datetime
from tornado.web import HTTPError
from yasmine.app.utils.imp_exp import ConvertToInventory
from slugify import slugify


class XmlService(HandlerMixin):
    def update_timestamp(self, xml_id):
        self.db.query(XmlModel) \
            .filter(XmlModel.id == xml_id) \
            .update({'updated_at': datetime.utcnow()})

    def validate(self, xml_id):
        try:
            inv = ConvertToInventory(xml_id, self).run()
        except Exception as e:
            raise HTTPError(reason="Unable to build XML: '%s'" % str(e))

        errors = []
        xml = self.db.query(XmlModel).get(xml_id)
        file = os.path.join(TMP_ROOT, f"{slugify(xml.name)}_{xml_id}.xml")
        if os.path.exists(file):
            os.remove(file)
        try:
            inv.write(file, format="STATIONXML", validate=True)
        except Exception as e:
            for x in e.args:
                errors.append(x)

        return errors

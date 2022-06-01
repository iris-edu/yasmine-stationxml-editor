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
from yasmine.app.enums.xml_node import XmlNodeEnum
from yasmine.app.handlers.base import AsyncThreadMixin, BaseHandler
from yasmine.app.models import ConfigModel
from yasmine.app.models import XmlNodeAttrRelationModel
from sqlalchemy.orm import joinedload

from yasmine.app.utils.inv_valid import VALIDATION_RULES, ValueRequired


class ConfigHandler(AsyncThreadMixin, BaseHandler):
    def async_get(self, db_id, **__):
        data = {'id': int(db_id)}
        for item in self.db.query(ConfigModel).all():
            data['%s__%s' % (item.group, item.name)] = item.value_obj
        return data

    def async_put(self, *_, **__):
        request_params = self.request_params
        with self.db.begin():
            for key, value in request_params.items():
                if key not in ['id']:
                    group, name = key.split('__')
                    record = self.db.query(ConfigModel).filter(ConfigModel.group == group, ConfigModel.name == name).first()
                    record.value_obj = value
        # to reset configuration
        self.application.__config__ = None
        return {'success': True}


class AttributeHandler(AsyncThreadMixin, BaseHandler):
    def async_get(self, node_id, **__):

        node_attrs = self.db.query(XmlNodeAttrRelationModel)\
            .join(XmlNodeAttrRelationModel.attr)\
            .options(joinedload(XmlNodeAttrRelationModel.attr))\
            .filter(XmlNodeAttrRelationModel.node_id == node_id)\
            .all()

        data = []
        for item in node_attrs:
            data.append({
                'id': item.attr.name,
                'is_critical': self._is_required_critical(int(node_id), item.attr.name)
            })
        return data

    @staticmethod
    def _is_required_critical(node_id, attr_name):
        rules = VALIDATION_RULES.get(node_id, {}).get(attr_name, [])
        for rule in rules:
            if isinstance(rule, ValueRequired) and rule.critical:
                return True
        return False

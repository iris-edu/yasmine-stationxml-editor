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


from yasmine.app.handlers.base import AsyncThreadMixin, BaseHandler
from yasmine.app.handlers.base import ExtJsHandler
from yasmine.app.models.user_library import UserLibraryModel
from yasmine.app.services.node_service import NodeService


class GridHandler(ExtJsHandler):
    model = UserLibraryModel


class NodeHandler(AsyncThreadMixin, BaseHandler):
    def async_post(self, *_, **__):
        params = self.request_params
        library_id = int(params['libraryId'])
        node_type = int(params['nodeType'])
        parent_node_id = int(params['parentNodeId']) if params['parentNodeId'] else None
        node_id_to_clone = int(params['nodeIdToClone']) if params['nodeIdToClone'] else None

        node_service = NodeService(self)
        if node_id_to_clone:
            new_node_id = node_service.add_node_to_library(library_id, node_id_to_clone)
        else:
            new_node_id = node_service.create_default_node_for_library(library_id, node_type, parent_node_id)

        return {'success': True, 'data': new_node_id}

    def async_get(self, library_id, node_type, node_inst_id, *_, **__):
        return NodeService(self).load_node_from_library(library_id, node_type, node_inst_id)

    def async_delete(self, library_id, node_type, node_inst_id, *_, **__):
        NodeService(self).delete_node_from_library(library_id, node_type, node_inst_id)
        return {'success': True}

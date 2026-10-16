/* ****************************************************************************
* 2026-09-27, version 4.4.0-beta: ASGSR, Alexey Emanov
*
* This file is part of the yasmine editing tool.
*
* yasmine (Yet Another Station Metadata INformation Editor), a tool to
* create and edit station metadata information in FDSN stationXML format,
* is a common development of IRIS and RESIF.
* Development and addition of new features is shared and agreed between * IRIS and RESIF.
*
*
* Version 1.0 of the software was funded by SAGE, a major facility fully
* funded by the National Science Foundation (EAR-1261681-SAGE),
* development done by ISTI and led by IRIS Data Services.
* Version 2.0 of the software was funded by CNRS and development led by * RESIF.
*
* This program is free software; you can redistribute it
* and/or modify it under the terms of the GNU Lesser General Public
* License as published by the Free Software Foundation; either
* version 3 of the License, or (at your option) any later version. *
* This program is distributed in the hope that it will be
* useful, but WITHOUT ANY WARRANTY; without even the implied warranty
* of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
* GNU Lesser General Public License (GNU-LGPL) for more details. *
* You should have received a copy of the GNU Lesser General Public
* License along with this software. If not, see
* <https://www.gnu.org/licenses/>
*
*
* ****************************************************************************/


Ext.define('yasmine.services.NodeService', {
  statics: {
    createNode: function (xmlId, parentNodeId, nodeType) {
      let parentId = (parentNodeId) ? parentNodeId : '';
      return Ext.Ajax.request({
        method: 'POST',
        url: `/api/xml/tree/${xmlId}/${parentId}`,
        jsonData: {
          node_inst_id: 0,
          parentId: parentNodeId,
          nodeType: nodeType
        },
      });
    },
    addNodeFromLibrary: function (xmlId, parentNodeId, nodeType, libraryNodeId) {
      let parentId = (parentNodeId) ? parentNodeId : '';
      return Ext.Ajax.request({
        method: 'POST',
        url: `/api/xml/tree/${xmlId}/${parentId}`,
        jsonData: {
          node_inst_id: libraryNodeId,
          parentId: parentNodeId,
          nodeType: nodeType
        },
      });
    },
    deleteNode: function (xmlId, nodeInstanceId) {
      return Ext.Ajax.request({
        method: 'DELETE',
        url: `/api/xml/tree/${xmlId}/${nodeInstanceId}`
      });
    },
    loadExtensions: function (xmlId, nodeInstanceId) {
      return Ext.Ajax.request({
        method: 'GET',
        url: `/api/xml/extensions/${xmlId}/${nodeInstanceId}/`
      }).then((response) => {
        return yasmine.services.NodeService.parseJson(response);
      }).then((result) => result && result.success ? result.data : null);
    },
    loadLibraryExtensions: function (libraryId, nodeInstanceId) {
      return Ext.Ajax.request({
        method: 'GET',
        url: `/api/user-library/extensions/${libraryId}/${nodeInstanceId}/`
      }).then((response) => {
        return yasmine.services.NodeService.parseJson(response);
      }).then((result) => result && result.success ? result.data : null);
    },
    loadNodeAttributes: function (nodeInstanceId) {
      return Ext.Ajax.request({
        method: 'GET',
        url: `/api/xml/attr/`,
        params: {filter: JSON.stringify([{property: 'node_inst_id', value: nodeInstanceId}])},
      }).then((response) => {
        return yasmine.services.NodeService.parseJson(response);
      }).then((result) => result && result.success ? result.data : null);
    },
    findSimilarChannel: function (xmlId, nodeInstanceId) {
      return Ext.Ajax.request({
        method: 'GET',
        url: `/api/xml/similar-channel/`,
        params: {xmlId, nodeInstanceId},
      }).then((response) => {
        return yasmine.services.NodeService.parseJson(response);
      }).then((result) => result && result.success ? result.data : null);
    },
    findNodePath: function (nodeId) {
      return Ext.Ajax.request({
        method: 'GET',
        url: `/api/xml/node-path/`,
        params: {nodeId},
      }).then((response) => {
        return yasmine.services.NodeService.parseJson(response);
      }).then((result) => result && result.success ? result.data : null);
    },
    parseJson: function (response) {
      try {
        return JSON.parse((response && response.responseText) || '{}');
      } catch (e) {
        return null;
      }
    },
    parentIdFromPath: function (path) {
      if (!path || path.length < 2) {
        return 0;
      }
      return path[path.length - 2].id;
    },
    findParent: function (nodeId) {
      let response = Ext.Ajax.request({
        method: 'GET',
        async: false,
        url: `/api/xml/node-path/`,
        params: {nodeId},
      });
      let parsed = yasmine.services.NodeService.parseJson(response);
      let result = parsed && parsed.data ? parsed.data.path : null;
      return yasmine.services.NodeService.parentIdFromPath(result);
    },
  }
})

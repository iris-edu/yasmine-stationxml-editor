/* ****************************************************************************
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
* 2019/10/07 : version 2.0.0 initial commit
*
* ****************************************************************************/


Ext.define("yasmine.utils.XmlNodeUtil", {
  singleton: true,
  isPlainValue: function (node) {
    let nodeData = node.data;
    if (!nodeData[nodeData.key]) {
      return true;
    }
    return (!nodeData[nodeData.key]['children'] && typeof (nodeData[nodeData.key]) !== 'object');
  },
  isArrayValue: function (node) {
    let nodeData = node.data;
    return (nodeData[nodeData.key]['children'] &&
      Array.isArray(nodeData[nodeData.key].children) &&
      nodeData[nodeData.key].children.length === 1 &&
      nodeData[nodeData.key].children[0] !== Object(nodeData[nodeData.key].children[0]));
  },
  canHaveValue: function (node) {
    let nodeData = node.data;

    if (!nodeData[nodeData.key]) {
      return true
    }

    if (!nodeData[nodeData.key]['children']) {
      return true
    }

    if (!Array.isArray(nodeData[nodeData.key].children)) {
      return true
    }

    if (nodeData[nodeData.key].children.length === 0) {
      return true
    }

    return nodeData[nodeData.key].children[0] !== Object(nodeData[nodeData.key].children[0]);
  },
  getValue: function (node) {
    let nodeData = node.data;

    if (!nodeData[nodeData.key]) {
      return null;
    }

    if (!nodeData[nodeData.key]['children'] && typeof (nodeData[nodeData.key]) !== 'object') {
      return nodeData[nodeData.key].toString();
    }

    if (nodeData[nodeData.key]['children'] &&
      Array.isArray(nodeData[nodeData.key].children) &&
      nodeData[nodeData.key].children.length === 1 &&
      nodeData[nodeData.key].children[0] !== Object(nodeData[nodeData.key].children[0])) {
      return nodeData[nodeData.key].children[0].toString();
    }
  },
  canAddNode: function (selectedNode) {
    if (!selectedNode || selectedNode.isRoot()) {
      return true;
    }

    return !this.getValue(selectedNode);
  },
  getNodeTitle: function (node) {
    let title = `<span>${node.data.key}</span>`;
    let value = this.getValue(node);
    return value ? `{title}: <b>${value}</b>` : title ;
  }
});

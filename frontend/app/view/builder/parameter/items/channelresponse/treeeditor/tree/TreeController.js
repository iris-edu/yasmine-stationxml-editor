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


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.tree.TreeController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.channel-response-tree',
  id: 'channel-response-tree-controller',
  listen: {
    controller: {
      '#channel-response-attribute-editor-controller': {
        onAttributeUpdated: 'onAttributeUpdated',
        onAttributeDeleted: 'onAttributeDeleted'
      },
      '#channel-response-value-editor-controller': {
        onNodenameUpdated: 'onNodeNameUpdated',
        onNodevalueUpdated: 'onNodeValueUpdated'
      }
    }
  },
  onExpandAll: function () {
    this.getView().getStore().getRoot().expandChildren(true);
  },
  onCollapseAll: function () {
    let rootNode = this.getView().getStore().getRoot();
    this.getView().setSelection(rootNode);
    this.fireEvent('responseNodeSelected', this.getSelectedRecord());
    this.getView().getStore().getRoot().collapseChildren(true);
  },
  onAddNewNodeClick: function () {
    let nodeName = this.getViewModel().get('newNodeName');
    let selectedNode = this.getSelectedRecord();
    let newNode = selectedNode.createNode({
      name: nodeName,
      text: nodeName,
      iconCls: 'fa-code',
      isattr: false,
      leaf: true
    });
    selectedNode.appendChild(newNode);
    selectedNode.expand();

    this.getViewModel().set('newNodeName', null);

    this.initNodeData(nodeName, newNode);

    this.fireEvent('responseNodeSelected', selectedNode);
  },
  onDeleteClick: function () {
    let node = this.getViewModel().get('selectedResponseNode');
    let nodeName = node.data.key;
    Ext.MessageBox.confirm(`Delete '${nodeName}' node`, `Are you sure you want to delete '${nodeName}'?`, function (btn) {
      if (btn === 'yes') {
        this.deleteNode();
      }
    }, this);
  },
  onAttributeUpdated: function (attributes) {
    let selectedNode = this.getSelectedRecord();
    let nodeData = selectedNode.data;
    let newAttr = {};
    attributes.forEach(x => {
      newAttr[x.name] = x.value;
    });

    if (!nodeData[nodeData.key]) {
      nodeData[nodeData.key] = {};
    }

    if (nodeData[nodeData.key]['attributes']) {
      nodeData[nodeData.key]['attributes'] = newAttr;
      return;
    }

    if (yasmine.utils.XmlNodeUtil.isPlainValue(selectedNode)) {
      let value = nodeData[nodeData.key];
      nodeData[nodeData.key] = {
        children: [value],
        attributes: newAttr
      };
      return;
    }

    nodeData[nodeData.key]['attributes'] = newAttr;
  },
  onAttributeDeleted: function (record) {
    let selectedNode = this.getSelectedRecord();
    let nodeData = selectedNode.data;
    let attr = nodeData[nodeData.key]['attributes'];
    delete attr[record.get('name')];
  },
  onNodeValueUpdated: function (record) {
    let selectedNode = this.getSelectedRecord();
    let nodeData = selectedNode.data;
    let nodeName = `<span>${nodeData.key}</span>`;
    selectedNode.set('text', record.get('value') ? `${nodeName}:&nbsp;<b>${record.get('value')}</b>` : nodeName);

    if (yasmine.utils.XmlNodeUtil.isPlainValue(selectedNode)) {
      nodeData[nodeData.key] = record.get('value');
    } else if (yasmine.utils.XmlNodeUtil.isArrayValue(selectedNode)) {
      nodeData[nodeData.key].children[0] = record.get('value');
    }

    let parentNode = selectedNode.parentNode;
    if (parentNode && !parentNode.isRoot()) {
      parentNode.data[parentNode.data.key].children = parentNode.data.children;

      while (parentNode.parentNode && parentNode.parentNode.data.key) {
        parentNode = parentNode.parentNode;
        parentNode.data[parentNode.data.key].children = parentNode.data.children;
      }
    }

    this.getViewModel().set('canAddNewNode', yasmine.utils.XmlNodeUtil.canAddNode(selectedNode));
  },
  onNodeNameUpdated: function (record) {
    let selectedNode = this.getSelectedRecord();
    let nodeData = selectedNode.data;
    let oldName = record.previousValues.name;
    let newName = record.get('name');
    if (nodeData.hasOwnProperty(oldName)) {
      nodeData[newName] = nodeData[oldName];
      nodeData.key = newName;
      delete nodeData[oldName];
      selectedNode.set('text', yasmine.utils.XmlNodeUtil.getNodeTitle(selectedNode));
    }
  },
  deleteNode: function () {
    let node = this.getSelectedRecord();
    let parentNode = node.parentNode;
    node.remove();
    node.destroy();

    let nodeDataIndex = parentNode.data.children.map(x => x.id).indexOf(node.id);
    delete parentNode.data.children[nodeDataIndex];

    this.getView().setSelection(parentNode);
    this.fireEvent('responseNodeSelected', this.getSelectedRecord());
  },
  getSelectedRecord: function () {
    return this.getView().getSelection()[0];
  },
  initNodeData: function (nodeName, node) {
    node.data.key = nodeName;
    node.data[nodeName] = null;

    let parentNode = node.parentNode;

    if (!parentNode.data['children']) {
      parentNode.data['children'] = [];
    }
    parentNode.data['children'].push(node.data);

    if (!parentNode.data[parentNode.data.key]) {
      parentNode.data[parentNode.data.key] = {
        children: []
      };
    }

    parentNode.data[parentNode.data.key]['children'].push(node.data);
  },

  onResponseNodeSelect: function () {
    this.fireEvent('responseNodeSelected', this.getSelectedRecord());
  }
});

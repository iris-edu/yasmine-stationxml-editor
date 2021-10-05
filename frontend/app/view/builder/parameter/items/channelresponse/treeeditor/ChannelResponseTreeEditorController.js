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


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.ChannelResponseTreeEditorController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.channel-response-tree-editor',
  listen: {
    controller: {
      '#channel-response-tree-controller': {
        responseNodeSelected: 'onNodeSelected'
      },
      '#parameter-editor-controller': {
        saveRecordError: 'onSaveRecordError'
      }
    }
  },
  initViewModel: function () {
    this.loadChannelResponseForEditing();
  },
  fillRecord: function () {
    let store = this.lookup('channelresponsetree').getStore();
    let rootNode = store.getRoot();
    let record = this.getViewModel().get('record');
    let nodeId = record.get('nodeId');
    record.set('value', { nodeId, response: this.prepareResponse(rootNode.data.children) });
  },
  onSaveRecordError: function (message) {
    Ext.MessageBox.show({
      title: 'Please fix response',
      msg: message,
      buttons: Ext.MessageBox.OK,
      icon: Ext.MessageBox['ERROR']
    });
  },
  loadChannelResponseForEditing: function () {
    let record = this.getViewModel().get('record');
    let nodeInstanceId = record.get('node_inst_id');
    let that = this;

    Ext.Ajax.request({
      method: 'GET',
      params: {nodeInstanceId},
      url: `/api/channel/response/xml/`,
      success: function (response, options) {
        let result = JSON.parse(response.responseText);
        if (!result.success) {
          Ext.MessageBox.show({
            title: 'An error occurred',
            msg: result.message,
            buttons: Ext.MessageBox.OK,
            icon: Ext.MessageBox['ERROR']
          });
        } else {
          that.getViewModel().set('channelResponse', result.data);
          let response = result.data;
          let responseChildren = response.Response.children;
          for (let child of responseChildren) {
            that.convertResponseTreeStore(child);
          }
          let responseTreeStore = Ext.create('Ext.data.TreeStore', {
            root: {
              iconCls: 'fa-code',
              expanded: true,
              text: 'Response',
              children: responseChildren
            }
          });
          let responseTree = that.lookupReference('channelresponsetree');
          responseTree.setStore(responseTreeStore);
        }
      }
    });
  },
  prepareResponse: function(responseNodes) {
    let children = [];
    for (let child of responseNodes) {
      if (child) {
        children.push(this.prepareResponseNode(child));
      }
    }

    return { "Response": { "children": children }};
  },
  prepareResponseNode: function(responseNode) {
    if (!responseNode.key) {
      if (responseNode !== Object(responseNode)) {
        return responseNode;
      }

      return null;
    }

    let result = {};
    result[responseNode.key] = {};
    let children = [];

    if (responseNode[responseNode.key]['children']) {
      for (let child of responseNode[responseNode.key]['children']) {
        children.push(this.prepareResponseNode(child));
      }
    } else {
      result[responseNode.key] = responseNode[responseNode.key];
    }

    if (children.length) {
      result[responseNode.key]['children'] = children;
    }

    if (responseNode[responseNode.key]['attributes']) {
      result[responseNode.key]['attributes'] = responseNode[responseNode.key]['attributes'];
    }

    return result;
  },
  convertResponseTreeStore: function (responseNode) {
    responseNode.iconCls = 'fa-code';
    let nodeName = Object.keys(responseNode)[0];
    if (nodeName) {
      if (responseNode[nodeName] !== Object(responseNode[nodeName])) {
        responseNode.text = '<span>' + nodeName + '</span>:&nbsp;' + '<span style="font-weight: bold;">' + responseNode[nodeName] + '</span>';
      } else if (responseNode[nodeName].children &&
        Array.isArray(responseNode[nodeName].children) &&
        responseNode[nodeName].children.length === 1 &&
        responseNode[nodeName].children[0] !== Object(responseNode[nodeName].children[0])) {
        responseNode.text = '<span>' + nodeName + '</span>:&nbsp;' + '<span style="font-weight: bold;">' + responseNode[nodeName].children[0] + '</span>';
      } else {
        responseNode.text = nodeName;
      }
      responseNode.key = nodeName;

      if (responseNode[nodeName].children) {
        responseNode.children = responseNode[nodeName].children;
        for (let child of responseNode[nodeName].children) {
          let hasChild = this.convertResponseTreeStore(child);

          if (!hasChild) {
            responseNode.leaf = true;
          }
        }
      } else {
        responseNode.leaf = true;
      }

      return true;
    } else {
      return false
    }
  },
  onNodeSelected: function (node) {
    let valuePanel = this.lookupReference('channel-response-value-editor');
    valuePanel.getStore().removeAll();
    valuePanel.getController().setNodeName(null);

    let attributePanel = this.lookupReference('channel-response-attribute-editor');
    attributePanel.getStore().removeAll();
    attributePanel.getController().setNodeName(null);

    this.getViewModel().set('canAddNewNode', yasmine.utils.XmlNodeUtil.canAddNode(node));
    this.getViewModel().set('selectedResponseNode', null);

    if (node.isRoot()) {
      return;
    }

    attributePanel.getController().setNodeName(node.get('key'));
    valuePanel.getController().setNodeName(node.get('key'));
    this.getViewModel().set('selectedResponseNode', node);

    let nodeData = node.data;
    let nodeName = nodeData.key;
    let nodeValue = yasmine.utils.XmlNodeUtil.getValue(node);
    let canNodeHaveValue = yasmine.utils.XmlNodeUtil.canHaveValue(node);
    valuePanel.getController().setRecord(nodeName, nodeValue, canNodeHaveValue);

    if (!nodeData[nodeData.key]) {
      return;
    }

    for (let attr in nodeData[nodeData.key]['attributes']) {
      let attrVal = nodeData[nodeData.key]['attributes'][attr].toString();
      attributePanel.getController().addRecord(attr, attrVal);
    }
  }

});

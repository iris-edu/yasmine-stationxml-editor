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


Ext.define('yasmine.view.xml.builder.children.tree.ChildrenTreeController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.children-tree',
  listen: {
    store: {
      '#treeStore': {
        nodebeforeexpand: 'onBeforeExpand'
      }
    }
  },

  init: function () {
    yasmine.Globals.LocationColorScale = d3.scaleOrdinal(d3.schemeCategory10);
    Ext.ux.Mediator.on('epoch-selected', this.onEpochSelected, this);
    Ext.ux.Mediator.on('node-updated', this.onNodeUpdated, this);
    Ext.ux.Mediator.on('node-created', this.onNodeCreated, this);
    Ext.ux.Mediator.on('node-deleted', this.onNodeDeleted, this);
    Ext.ux.Mediator.on('children-reload', this.onChildrenReload, this);
  },
  onBeforeExpand: function (node) {
    let viewModel = this.getViewModel();
    viewModel.set('storeNodeType', yasmine.utils.NodeTypeConverter.getChild(node.get('nodeType')));
    viewModel.notify();
  },
  onTreeNodeSelect: function () {
    let selectedItem = this._getSelectedRecord();
    Ext.ux.Mediator.fireEvent('node-selected', selectedItem.getData());
  },
  onEpochSelected: function (epoch) {
    let store = this.getStore('treeStore');
    store.clearFilter(true);
    if (epoch) {
      store.addFilter([{property: 'epoch', value: Ext.Date.format(epoch, yasmine.Globals.DateReadFormat)}]);
    }
    store.load();
  },
  onChildrenReload: function (storeNodeType) {
    let viewModel = this.getViewModel();
    viewModel.set('storeNodeType', storeNodeType);
    viewModel.set('selectedItem', null);
    viewModel.notify();
    Ext.ux.Mediator.fireEvent('node-selected', null);
    this._getViewModelStore().reload();
  },
  onNodeUpdated: function () {
    this._reloadParentNode();
  },
  onNodeCreated: function () {
    this._reloadCurrentNode();
  },
  onNodeDeleted: function (nodeId) {
    let node = this._getNode(nodeId);
    let parentNode = this._getNode(node.get('parentId'));
    this.getViewModel().set('selectedItem', parentNode);
    Ext.ux.Mediator.fireEvent('node-selected', parentNode.getData());
    node.remove();
  },
  _reloadCurrentNode: function () {
    let node = this._getSelectedRecord();
    let viewModel = this.getViewModel();
    viewModel.set('storeNodeType', yasmine.utils.NodeTypeConverter.getChild(node.get('nodeType')));
    viewModel.notify();
    this._getViewModelStore().load({
      node: node,
      callback: (children) => {
        node.set('has_children', children.length > 0);
        node.set('leaf', children.length === 0);
        node.expand();
      }
    });
  },
  _reloadParentNode: function () {
    let node = this._getSelectedRecord();
    let parentNode = this._getNode(node.get('parentId'));
    let viewModel = this.getViewModel();
    viewModel.set('storeNodeType', node.get('nodeType'));
    viewModel.notify();
    this._getViewModelStore().load({
      node: parentNode,
      callback: (children) => {
        this.getViewModel().set('selectedItem', this._getNode(node.get('id')))
        parentNode.set('has_children', children.length > 0);
        parentNode.set('leaf', children.length === 0);
      }
    });
  },
  _getSelectedRecord: function () {
    return this.getView().getSelection()[0];
  },
  _getViewModelStore: function () {
    return this.getViewModel().getStore('treeStore');
  },
  _getNode: function (nodeId) {
    return this.getStore('treeStore').findNode('id', nodeId);
  }
});

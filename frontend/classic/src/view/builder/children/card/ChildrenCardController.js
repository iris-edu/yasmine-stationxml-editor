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


Ext.define('yasmine.view.xml.builder.children.card.ChildrenCardController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.children-card',
  listen: {
    store: {
      '#childrenStore': {
        beforeload: 'onChildrenBeforeLoad'
      }
    }
  },
  init: function () {
    yasmine.Globals.LocationColorScale = d3.scaleOrdinal(d3.schemeCategory10);
    Ext.ux.Mediator.on('epoch-selected', this.onEpochSelected, this);
    Ext.ux.Mediator.on('node-updated', this.onNodeUpdated, this);
    Ext.ux.Mediator.on('node-created', this.onNodeCreated, this);
    Ext.ux.Mediator.on('node-deleted', this.onNodeDeleted, this);
    Ext.ux.Mediator.fireEvent('node-selected', this._getRoot());
    Ext.ux.Mediator.on('children-reload', this.onChildrenReload, this);
  },
  onNodeUpdated: function () {
    this._reloadSelectedNode();
  },
  onNodeCreated: function () {
    let selectedItem = this.getViewModel().get('selectedItem');
    if (!selectedItem) {
      this._reloadStore();
    } else {
      this._reloadSelectedNode();
    }
  },
  onChildrenReload: function (storeNodeType) {
    let viewModel = this.getViewModel();
    viewModel.set('storeNodeType', storeNodeType);
    viewModel.set('selectedItem', null);
    viewModel.notify();
    Ext.ux.Mediator.fireEvent('node-selected', null);
    this._reloadStore();
  },
  onNodeDeleted: function () {
    this._reloadStore();
  },
  onChildrenBeforeLoad: function (store) {
    store.removeAll();
    let parentNodeId = this.getViewModel().get('parentNodeId');
    if (parentNodeId > 0) {
      store.add(new yasmine.view.xml.builder.children.card.Item({type: 'back'}));
    }
  },
  onBeforeSelect: function (item, record) {
    return record.get('type') !== 'back';
  },
  onItemClick: function (item, record) {
    if (record.get('type') === 'back') {
      this._navigate(item, record)
    }
  },
  onItemDblClick: function (item, record) {
    if (!record.get('leaf') && record.get('type') !== 'back') {
      this._navigate(item, record);
    }
  },
  onItemSelectionChange: function (cmp, selected) {
    let record = null;
    if (selected.length > 0) {
      record = selected[0].getData();
    } else if (this.getViewModel().get('parentNodeId') === 0) {
      record = this._getRoot();
    }
    Ext.ux.Mediator.fireEvent('node-selected', record);
  },
  onItemKeyUp: function (view, record, item, index, event) {
    if (!record.get('leaf') && event.event.code === 'Enter') {
      this._navigate(view, record);
    }
  },
  onEpochSelected: function (epoch) {
    let store = this.getViewModel().getStore('childrenStore');
    store.clearFilter(true);
    if (epoch) {
      store.addFilter([{property: 'epoch', value: Ext.Date.format(epoch, yasmine.Globals.DateReadFormat)}]);
    }
    store.load({addRecords: true});
  },
  _navigate: function (item, record) {
    let parentId = record.id;
    let storeNodeType = record.get('nodeType') + 1;
    if (record.get('type') === 'back') {
      let parentNodeId = this.getViewModel().get('parentNodeId');
      parentId = yasmine.services.NodeService.findParent(parentNodeId);
      storeNodeType = this.getViewModel().get('storeNodeType');
      storeNodeType = yasmine.utils.NodeTypeConverter.getParent(storeNodeType);
    }
    this.getViewModel().set('parentNodeId', parentId);
    this.getViewModel().set('storeNodeType', storeNodeType);
    this.getViewModel().notify();
    this._reloadStore();
  },
  _reloadSelectedNode: function () {
    let store = this.getViewModel().getStore('childrenStore');
    let selectedNodeId = this.getViewModel().get('selectedItem').id;
    store.removeAll();
    store.load({
      addRecords: true,
      callback: (children) => {
        let node = children.find(x => x.id === selectedNodeId);
        this.getViewModel().set('selectedItem', node);
      }
    });
  },
  _reloadStore: function () {
    let store = this.getViewModel().getStore('childrenStore');
    store.removeAll();
    store.load({
      addRecords: true,
      callback: () => {
        let parentId = this.getViewModel().get('parentNodeId');
        Ext.ux.Mediator.fireEvent('node-selected', parentId === 0 ? this._getRoot() : null);
      }
    });
  },
  _getRoot: function () {
    return {id: 0, root: true, nodeType: 0};
  }
});

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


Ext.define('yasmine.view.userlibrary.builder.children.UserLibraryChildrenController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.userlibrary-children',
  requires: [
    'yasmine.view.userlibrary.builder.children.card.ChildrenCardModel',
    'yasmine.view.userlibrary.builder.children.tree.ChildrenTreeModel',
    'yasmine.view.xml.builder.children.tree.ChildrenTree',
    'yasmine.view.xml.builder.children.card.ChildrenCard',
  ],
  init: function () {
    Ext.ux.Mediator.on('node-selected', this.onNodeSelected, this);
    Ext.ux.Mediator.on('children-reload', this.onChildrenReload, this);
  },
  onNodeSelected: function (node) {
    this.getViewModel().set('selectedNode', node);
  },
  afterRender: function () {
    this.getView().removeAll();
    let builderViewMode = yasmine.Globals.BuilderViewMode;
    if (builderViewMode === yasmine.XMLViewModeEnum.tree) {
      this.createChildrenView('tree');
    } else if (builderViewMode === yasmine.XMLViewModeEnum.card) {
      this.createChildrenView('card');
    }
  },
  createChildrenView: function (name) {
    let modeView = Ext.create({
      xtype: `children-${name}`,
      viewModel: `userlibrary-children-${name}`
    });
    this.getView().add(modeView);
  },
  onChildrenReload: function (storeNodeType) {
    let viewModel = this.getViewModel();
    viewModel.set('libraryType', storeNodeType);
    viewModel.set('selectedNode', null);
    viewModel.notify();
  },
  onNodeCreateClick: function () {
    let viewModel = this.getViewModel();
    let selectedNode = viewModel.get('selectedNode');
    let nodeType = yasmine.utils.NodeTypeConverter.getChild(selectedNode.nodeType);
    if (selectedNode.root) {
      nodeType = viewModel.get('libraryType');
    }

    Ext.Ajax.request({
      url: '/api/user-library/node/',
      jsonData: {
        libraryId: viewModel.get('storeLibraryId'),
        nodeType: nodeType,
        parentNodeId: selectedNode.id,
        nodeIdToClone: null
      },
      method: 'POST',
      success: function (response) {
        let itemId = JSON.parse(response.responseText).data;
        if (selectedNode.root) {
          Ext.ux.Mediator.fireEvent('children-reload', nodeType);
        } else {
          Ext.ux.Mediator.fireEvent('node-created', itemId);
        }
      }
    });
  },
  onNodeDeleteClick: function () {
    let selectedItem = this.getViewModel().get('selectedNode');
    Ext.MessageBox.confirm('Confirm', `Are you sure you want to delete a selected ${selectedItem.name}?`, function (btn) {
      if (btn === 'yes') {
        this.deleteSelectedNode();
      }
    }, this);
  },
  deleteSelectedNode: function () {
    let viewModel = this.getViewModel();
    let selectedNode = viewModel.get('selectedNode');
    let storeLibraryId = viewModel.get('storeLibraryId');
    let storeNodeType = selectedNode.nodeType;
    Ext.Ajax.request({
      url: `/api/user-library/node/${storeLibraryId}/${storeNodeType}/${selectedNode.id}`,
      method: 'DELETE',
      success: function () {
        Ext.ux.Mediator.fireEvent('node-deleted', selectedNode.id);
      }
    });
  },
})

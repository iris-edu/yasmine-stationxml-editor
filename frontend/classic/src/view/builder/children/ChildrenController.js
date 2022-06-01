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


Ext.define('yasmine.view.xml.builder.children.ChildrenController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.children',
  requires: [
    'yasmine.view.xml.builder.children.tree.ChildrenTree',
    'yasmine.view.xml.builder.children.card.ChildrenCard'
  ],
  init: function () {
    Ext.ux.Mediator.on('node-selected', this.onNodeSelected, this);
    Ext.ux.Mediator.on('node-updated', this.onNodeSelected, this);
    this._createView();
  },
  onNodeSelected: function (node) {
    if (node == null) {
      return;
    }
    yasmine.services.NodeService.findNodePath(node.id).then((data) => {
      let path = data.path.map(function (item) {
        let icon = yasmine.utils.NodeTypeConverter.toIcon(item.nodeType);
        return `<a class="${icon}" aria-hidden="true"></a> ${item.code}`;
      });

      let title = path.join('<a style="margin-left: 7px; margin-right: 7px; " class="x-fa fa-chevron-right" aria-hidden="true"></a>');
      this.getViewModel().set('title', title);
    });
  },
  _createView: function () {
    let builderViewMode = yasmine.Globals.BuilderViewMode;
    if (builderViewMode === yasmine.XMLViewModeEnum.tree) {
      this._createChildrenView('children-tree');
    } else if (builderViewMode === yasmine.XMLViewModeEnum.card) {
      this._createChildrenView('children-card');
    }
  },
  _createChildrenView: function (name) {
    this.getView().removeAll();
    let modeView = Ext.create({xtype: name});
    this.getView().add(modeView);
  },
});

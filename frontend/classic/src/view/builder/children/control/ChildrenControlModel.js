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
* 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.children.control.ChildrenControlModel', {
  extend: 'Ext.app.ViewModel',
  alias: 'viewmodel.children-control',
  data: {
    selectedNode: null,
    selectedEpoch: null,
    extractNodeMenu: [],
    insertNodeMenu: []
  },
  stores: {
    epochStore: {
      storeId: 'epochStore',
      model: 'yasmine.view.xml.builder.children.control.Date',
      autoLoad: false,
      proxy: {
        type: 'rest',
        url: '/api/xml/epoch/{xmlId}/',
        paramsAsJson: true
      }
    },
    userLibraryStore: {
      model: 'yasmine.model.UserLibrary',
      autoLoad: false,
      remoteFilter: true,
      autoSync: false
    }
  },
  formulas: {
    canCreateChild: function (get) {
      let selectedNode = get('selectedNode');
      if (!selectedNode) {
        return false;
      }
      return selectedNode.nodeType !== yasmine.NodeTypeEnum.channel;
    },
    canDeleteCurrent: function (get) {
      let selectedNode = get('selectedNode');
      if (!selectedNode) {
        return false;
      }
      return !selectedNode.root;
    },
    canShowMap: function (get) {
      let selectedNode = get('selectedNode');
      if (!selectedNode) {
        return false;
      }
      if (selectedNode.id === 0 || selectedNode.root) {
        return true;
      }
      let nodeType = selectedNode.nodeType;
      return nodeType === yasmine.NodeTypeEnum.network ||
        nodeType === yasmine.NodeTypeEnum.station ||
        nodeType === yasmine.NodeTypeEnum.channel;
    },
    canTemplate: function (get) {
      let selectedNode = get('selectedNode');
      if (!selectedNode) {
        return false;
      }
      return !selectedNode.root;
    },
    childNodeTitle: function (get) {
      let selectedNode = get('selectedNode');
      if (!selectedNode) {
        return;
      }
      return yasmine.utils.NodeTypeConverter.getChildTitle(selectedNode.nodeType);
    },
    currentNodeTitle: function (get) {
      let selectedNode = get('selectedNode');
      if (!selectedNode) {
        return;
      }
      return yasmine.utils.NodeTypeConverter.getTitle(selectedNode.nodeType);
    }
  }
});

Ext.define('yasmine.view.xml.builder.children.control.Date', {
  extend: 'yasmine.model.CollectionItem',
  fields: [
    {name: 'date', type: 'date', persist: false, dateFormat: yasmine.Globals.DateReadFormat},
    {
      name: 'dateString',
      type: 'string',
      persist: false,
      depends: ['date'],
      convert: function (value, record) {
        let date = record.get('date');
        return date ? Ext.Date.format(date, yasmine.Globals.DatePrintLongFormat) : null;
      }
    }
  ]
});

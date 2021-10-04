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


Ext.define('yasmine.view.xml.XmlList', {
  extend: 'Ext.grid.Panel',
  xtype: 'xml-list',
  requires: [
    'Ext.toolbar.Paging',
    'Ext.grid.filters.Filters',
    'yasmine.view.xml.list.XmlListController',
    'yasmine.view.xml.list.XmlListModel'
  ],
  title: 'XML',
  frame: true,
  plugins: 'gridfilters',
  controller: 'xml-list',
  viewModel: 'xml-list',
  bind: {
    selection: '{theRow}',
    store: '{listStore}'
  },
  actions: {
    sell: {
      iconCls: 'fa fa-database'
    }
  },
  viewConfig: {
    loadMask: false
  },
  columns: {
    defaults: {
      flex: 1
    },
    items: [
      {text: 'Name', dataIndex: 'name', filter: {type: 'string'}},
      {text: 'Source', dataIndex: 'source', filter: {type: 'string'}},
      {text: 'Module', dataIndex: 'module', filter: {type: 'list'}, flex: 3},
      {text: 'Uri', dataIndex: 'uri', filter: {type: 'string'}, flex: 3},
      {text: 'Sender', dataIndex: 'sender', filter: {type: 'string'}},
      {
        text: 'Created at',
        dataIndex: 'created_at',
        xtype: 'datecolumn',
        filter: {type: 'date', dateFormat: yasmine.Globals.DatePrintLongFormat},
        format: yasmine.Globals.DatePrintLongFormat
      },
      {
        text: 'Updated at',
        dataIndex: 'updated_at',
        xtype: 'datecolumn',
        filter: {type: 'date', dateFormat: yasmine.Globals.DatePrintLongFormat},
        format: yasmine.Globals.DatePrintLongFormat
      }
    ]
  },
  tbar: [{
    itemId: 'createXmlId',
    tooltip: 'Create XML',
    iconCls: 'x-fa fa-plus',
    handler: 'onCreateXmlClick'
  }, {
    tooltip: 'Delete XML',
    itemId: 'deleteXmlId',
    iconCls: 'x-fa fa-minus',
    handler: 'onDeleteXmlClick',
    disabled: true,
    bind: {
      disabled: '{!theRow}'
    }
  }, {
    tooltip: 'Edit XML',
    iconCls: 'x-fa fa-pencil',
    handler: 'onEditXmlClick',

    disabled: true,
    bind: {
      disabled: '{!theRow}'
    }
  }, '-', {
    tooltip: 'XML Builder',
    iconCls: 'x-fa fa-wrench',
    handler: 'onBuildXmlClick',
    disabled: true,
    bind: {
      disabled: '{!theRow}'
    }
  }, '-', {
    tooltip: 'Import XML',
    iconCls: 'x-fa fa-download',
    handler: 'onImportXmlClick'
  }, {
    tooltip: 'Export as XML',
    iconCls: 'x-fa fa-upload',
    handler: 'onExportXmlClick',
    disabled: true,
    bind: {
      disabled: '{!theRow}'
    }
  }],
  listeners: {
    itemdblclick: 'onBuildXmlClick'
  },
  tools: [
    {
      type: 'help',
      handler: function () {
        yasmine.utils.HelpUtil.helpMe('xml_list', 'List of XMLs')
      }
    }
  ]
});

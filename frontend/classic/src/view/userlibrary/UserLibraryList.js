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


Ext.define('yasmine.view.userlibrary.UserLibrary', {
  extend: 'Ext.grid.Panel',
  xtype: 'userlibrary-list',
  requires: [
    'yasmine.view.userlibrary.UserLibraryListController',
    'yasmine.view.userlibrary.UserLibraryListModel'
  ],
  controller: 'userlibrary-list',
  viewModel: 'userlibrary-list',
  title: 'User Libraries',
  frame: true,
  bind: {
    selection: '{selectedUserLibrary}',
    store: '{userLibraryStore}'
  },
  plugins: [{
    ptype: 'rowediting',
    listeners: {
      canceledit: function (editor, opt) {
        if (opt.record.phantom && !opt.record.dirty) {
          editor.grid.store.remove(opt.record)
        }
      }
    }
  }],
  selModel: 'rowmodel',
  columns: [
    {
      text: 'Name',
      flex: 1,
      dataIndex: 'name',
      editor: {
        completeOnEnter: true,
        field: {
          xtype: 'textfield',
          allowBlank: false
        }
      }
    },
    {
      text: 'Created at',
      dataIndex: 'created_at',
      xtype: 'datecolumn',
      filter: { type: 'date', dateFormat: yasmine.Globals.DatePrintShortFormat },
      format: yasmine.Globals.DatePrintShortFormat
    },
    {
      text: 'Updated at',
      dataIndex: 'updated_at',
      xtype: 'datecolumn',
      filter: { type: 'date', dateFormat: yasmine.Globals.DatePrintShortFormat },
      format: yasmine.Globals.DatePrintShortFormat
    }
  ],
  listeners: {
    itemdblclick: 'onConfigureLibraryClick'
  },
  tbar: [
    {
      tooltip: 'Create a new library',
      iconCls: 'x-fa fa-plus',
      handler: 'onCreateLibraryClick'
    },
    {
      tooltip: 'Delete a selected library',
      iconCls: 'x-fa fa-minus',
      handler: 'onDeleteLibraryClick',
      disabled: true,
      bind: {
        disabled: '{!selectedUserLibrary}'
      }
    },
    {
      tooltip: 'Rename a selected library',
      iconCls: 'x-fa fa-pencil',
      handler: 'onEditLibraryClick',
      disabled: true,
      bind: {
        disabled: '{!selectedUserLibrary}'
      }
    },
    '-',
    {
      tooltip: 'Configure a selected library',
      iconCls: 'x-fa fa-wrench',
      handler: 'onConfigureLibraryClick',
      disabled: true,
      bind: {
        disabled: '{!selectedUserLibrary}'
      }
    }
  ]
});

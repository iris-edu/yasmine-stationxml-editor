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


Ext.define('yasmine.view.xml.builder.parameter.components.person.PersonList', {
  extend: 'Ext.grid.Panel',
  xtype: 'person-list',
  requires: [
    'yasmine.view.xml.builder.parameter.components.person.PersonListModel',
    'yasmine.view.xml.builder.parameter.components.person.PersonListController'
  ],
  viewModel: 'person-list',
  controller: 'person-list',
  bind: {
    store: '{personStore}',
    selection: '{selectedRow}'
  },
  style: 'border: solid #d0d0d0 1px',
  columns: [
    {
      text: 'Names',
      dataIndex: '_names',
      renderer: function (value) {
        if (value.length > 0) {
          return value.map(function (item) {
            return item._name
          }).join('; ');
        }

        return yasmine.Globals.NotApplicable;
      },
      flex: 1
    },
    {
      text: 'Emails',
      dataIndex: '_emails',
      renderer: function (value) {
        if (value.length > 0) {
          return value.map(function (item) {
            return item._email
          }).join('; ');
        }

        return yasmine.Globals.NotApplicable;
      },
      flex: 1
    },
    {
      text: 'Agencies',
      dataIndex: '_agencies',
      renderer: function (value) {
        if (value.length > 0) {
          return value.map(function (item) {
            return item._name
          }).join('; ');
        }

        return yasmine.Globals.NotApplicable;
      },
      flex: 1
    }
  ],
  listeners: {
    itemdblclick: 'onEditClick'
  },
  tbar: [
    {
      tooltip: 'Add Person',
      iconCls: 'x-fa fa-plus',
      handler: 'onAddClick'
    },
    {
      tooltip: 'Delete Person',
      disabled: true,
      bind: {
        disabled: '{!selectedRow}'
      },
      iconCls: 'x-fa fa-minus',
      handler: 'onDeleteClick',
    },
    {
      tooltip: 'Edit Person',
      disabled: true,
      bind: {
        disabled: '{!selectedRow}'
      },
      iconCls: 'x-fa fa-pencil',
      handler: 'onEditClick',
    },
    {xtype: 'container', flex: 1},
    {xtype: 'label', html: 'PERSONS'},
    {xtype: 'container', flex: 1}
  ]
});

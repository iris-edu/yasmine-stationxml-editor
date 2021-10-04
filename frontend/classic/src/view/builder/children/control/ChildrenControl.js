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


Ext.define('yasmine.view.xml.builder.children.control.ChildrenControl', {
  extend: 'Ext.toolbar.Toolbar',
  xtype: 'children-control',
  requires: [
    'yasmine.view.xml.builder.children.control.ChildrenControlController',
    'yasmine.view.xml.builder.children.control.ChildrenControlModel'
  ],
  viewModel: 'children-control',
  controller: 'children-control',
  items: [
    {
      iconCls: 'x-fa fa-plus',
      disabled: false,
      bind: {
        disabled: '{!canCreateChild}'
      },
      menu: [
        {
          iconCls: 'x-fa fa-sign-out fa-rotate-90',
          bind: {
            text: 'Add a <b>{childNodeTitle}</b> from a user library',
            menu: '{insertNodeMenu}'
          }
        },
        {
          iconCls: 'x-fa fa-magic',
          bind: {
            text: 'Add a <b>{childNodeTitle}</b> using a wizard'
          },
          handler: 'onWizardClick'
        },
        {
          iconCls: 'x-fa fa-plus',
          bind: {
            iconCls: '{nodeLevelIcon}',
            text: 'Add a default <b>{childNodeTitle}</b>'
          },
          handler: 'onAddDefaultClick'
        }
      ]
    },
    {
      xtype: 'button',
      iconCls: 'x-fa fa-minus',
      handler: 'onDeleteClick',
      disabled: true,
      bind: {
        tooltip: 'Delete a selected {currentNodeTitle}',
        disabled: '{!canDeleteCurrent}'
      }
    },
    '-',
    {
      iconCls: 'x-fa fa-sign-out fa-rotate-270',
      disabled: true,
      bind: {
        disabled: '{!canTemplate}',
        menu: '{extractNodeMenu}'
      },
    },
    '-',
    '->',
    '-',
    {
      xtype: 'combobox',
      width: 235,
      bind: {
        store: '{epochStore}',
        selection: '{selectedEpoch}'
      },
      triggers: {
        clear: {
          cls: 'x-form-clear-trigger',
          handler: 'onEpochClearClick'
        }
      },
      displayField: 'dateString',
      fieldLabel: 'Epoch',
      editable: false,
      labelWidth: 40,
      listeners: {
        select: 'onEpochSelect'
      },
      emptyText: 'Select Epoch'
    }
  ]
});

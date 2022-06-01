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


Ext.define('yasmine.view.xml.builder.parameter.items.operators.OperatorsEditorForm', {
  extend: 'Ext.window.Window',
  xtype: 'operators-editor-form',
  requires: [
    'yasmine.view.xml.builder.parameter.items.operators.OperatorsEditorFormModel',
    'yasmine.view.xml.builder.parameter.items.operators.OperatorsEditorFormController'
  ],
  controller: 'operators-editor-form',
  viewModel: 'operators-editor-form',
  title: 'Operators',
  modal: true,
  frame: true,
  width: 600,
  bodyPadding: 10,
  items: {
    xtype: 'form',
    layout: 'anchor',
    defaults: {
      anchor: '100%'
    },
    items: [
      {
        xtype: 'combobox',
        fieldLabel: '<b>GATITO</b>',
        bind: {
          store: '{helpStore}'
        },
        displayField: 'website',
        listeners: {
          select: 'onGatitoSelect'
        }
      },
      {
        hidden: true,
        bind: {
          html: '<b>{help}</b>',
          hidden: '{!help}'
        },
      },
      {
        flex: 1,
        xtype: 'textfield',
        itemId: 'focusItem',
        labelAlign: 'top',
        fieldLabel: 'Website',
        bind: '{website}'
      },
      {
        flex: 1,
        xtype: 'textfield',
        labelAlign: 'top',
        fieldLabel: 'Agency',
        bind: '{agency}'
      },
      {
        layout: {
          type: 'accordion'
        },
        margin: '-10 -5 10 -5',
        height: 400,
        items: [
          {
            xtype: 'person-list',
            title: 'Contacts',
            reference: 'operatorcontactgrid',
            margin: '20 0 0 0',
            flex: 1
          }
        ]
      }
    ],
    buttons: [{
      text: 'Save',
      handler: 'onSaveClick'
    }, {
      text: 'Cancel',
      handler: 'onCancelClick'
    }]
  }
});

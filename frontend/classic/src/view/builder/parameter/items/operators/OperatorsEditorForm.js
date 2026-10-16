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
* 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
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
  title: 'Operator',
  modal: true,
  frame: false,
  cls: 'yasmine-window yasmine-collection-window',
  layout: 'fit',
  minWidth: 280,
  tools: [{
    type: 'help',
    handler: 'onHelpClick'
  }],
  bodyPadding: 10,
  listeners: {
    show: function () {
      yasmine.utils.ResponsiveUtil.fitWindow(this, {
        minWidth: 400,
        minHeight: 360,
        width: 600,
        height: 560
      });
    },
    resize: function () {
      yasmine.utils.ResponsiveUtil.clampWindow(this);
    }
  },
  items: {
    xtype: 'form',
    layout: {
      type: 'vbox',
      align: 'stretch'
    },
    items: [
      {
        xtype: 'combobox',
        fieldLabel: '<b>GATITO templates</b>',
        labelAttrTpl: 'data-qtip="Generic ATomic lIbrary of Tiny Objects — pick a reusable Operator template"',
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
        xtype: 'textfield',
        itemId: 'focusItem',
        labelAlign: 'top',
        fieldLabel: 'Website',
        stationXmlRelativePath: 'WebSite',
        bind: '{website}'
      },
      {
        xtype: 'textfield',
        labelAlign: 'top',
        fieldLabel: 'Agency',
        stationXmlRelativePath: 'Agency',
        bind: '{agency}',
        allowBlank: false,
        allowOnlyWhitespace: false
      },
      {
        xtype: 'person-list',
        title: 'Contacts',
        reference: 'operatorcontactgrid',
        flex: 1,
        minHeight: 160
      }
    ],
    buttons: [{
      text: 'Save',
      iconCls: 'x-fa fa-floppy-o',
      cls: 'yasmine-primary-action',
      handler: 'onSaveClick'
    }, {
      text: 'Cancel',
      iconCls: 'x-fa fa-ban',
      handler: 'onCancelClick'
    }]
  }
});

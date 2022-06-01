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


Ext.define('yasmine.view.xml.builder.parameter.items.comments.CommentsEditorForm', {
  extend: 'Ext.window.Window',
  xtype: 'comments-editor-form',
  requires: [
    'yasmine.view.xml.builder.parameter.items.comments.CommentsEditorFormModel',
    'yasmine.view.xml.builder.parameter.items.comments.CommentsEditorFormController'],
  controller: 'comments-editor-form',
  viewModel: 'comments-editor-form',
  title: 'Comment',
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
        flex: 1,
        xtype: 'textfield',
        labelAlign: 'top',
        fieldLabel: 'Subject',
        bind: '{subject}'
      },
      {
        xtype: 'combobox',
        flex: 1,
        itemId: 'focusItem',
        fieldLabel: 'Comment',
        labelAlign: 'top',
        queryMode: 'local',
        displayField: 'searchText',
        valueField: 'value',
        bind: {
          store: '{commentHelpStore}',
          value: '{value}'
        },
        tpl: Ext.create('Ext.XTemplate',
          '<ul class="x-list-plain"><tpl for=".">',
          '<li role="option" class="x-boundlist-item"><b>{value}</b><br/><div style="line-height: 120%;">{description}</div></li>',
          '<hr>',
          '</tpl></ul>'
        ),
        displayTpl: Ext.create('Ext.XTemplate',
          '<tpl for=".">',
          '{value}',
          '</tpl>'
        ),
        listeners: {
          beforequery: function (record) {
            record.query = new RegExp(record.query, 'ig');
          }
        },
        listConfig: {
          listeners: {
            beforeshow: function (picker) {
              picker.minWidth = 600;
            }
          }
        },
      },
      {
        xtype: 'numberfield',
        labelAlign: 'top',
        fieldLabel: 'ID',
        minValue: 0,
        bind: '{id}'
      },
      {
        layout: 'hbox',
        items: [
          {
            xtype: 'datefield',
            flex: 1,
            labelAlign: 'top',
            padding: '0 5 0 0',
            format: yasmine.Globals.DatePrintLongFormat,
            fieldLabel: 'Effective Start Date',
            bind: '{beginEffectiveTime}',
            allowBlank: false
          },
          {
            xtype: 'datefield',
            flex: 1,
            labelAlign: 'top',
            padding: '0 0 0 5',
            format: yasmine.Globals.DatePrintLongFormat,
            fieldLabel: 'Effective End Date',
            bind: '{endEffectiveTime}',
            allowBlank: false
          }
        ]
      },
      {
        xtype: 'person-list',
        margin: '20 0 10 0',
        height: 300,
        flex: 1,
        reference: 'person-list'
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

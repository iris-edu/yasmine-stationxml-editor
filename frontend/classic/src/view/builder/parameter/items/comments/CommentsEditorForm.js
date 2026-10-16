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
* NRLv2 online support (2026): ASGSR, Alexey Emanov.
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
* 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.parameter.items.comments.CommentsEditorForm', {
  extend: 'Ext.window.Window',
  xtype: 'comments-editor-form',
  requires: [
    'yasmine.view.xml.builder.parameter.items.comments.CommentsEditorFormModel',
    'yasmine.view.xml.builder.parameter.items.comments.CommentsEditorFormController',
    'Ext.plugin.Responsive'
  ],
  controller: 'comments-editor-form',
  viewModel: 'comments-editor-form',
  title: 'Comment',
  modal: true,
  frame: false,
  cls: 'yasmine-window yasmine-collection-window',
  minWidth: 280,
  layout: 'fit',
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
        height: 520
      });
    },
    afterlayout: function () {
      yasmine.utils.ResponsiveUtil.clampWindow(this);
    }
  },
  items: {
    xtype: 'form',
    minWidth: 0,
    scrollable: 'y',
    layout: {
      type: 'vbox',
      align: 'stretch'
    },
    items: [
      {
        xtype: 'textfield',
        labelAlign: 'top',
        fieldLabel: 'Subject',
        stationXmlRelativePath: '@subject',
        bind: '{subject}'
      },
      {
        xtype: 'combobox',
        itemId: 'focusItem',
        fieldLabel: 'Value',
        stationXmlRelativePath: 'Value',
        labelAlign: 'top',
        allowBlank: false,
        allowOnlyWhitespace: false,
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
              picker.minWidth = yasmine.utils.ResponsiveUtil.fitMinWidth(600);
            }
          }
        },
      },
      {
        xtype: 'numberfield',
        labelAlign: 'top',
        fieldLabel: 'ID (optional)',
        stationXmlRelativePath: '@id',
        bind: '{id}',
        allowBlank: true,
        allowDecimals: false,
        minValue: 0
      },
      {
        layout: {
          type: 'hbox',
          align: 'stretch'
        },
        plugins: 'responsive',
        responsiveConfig: {
          'width < 768 || height < 500': {
            layout: {type: 'vbox', align: 'stretch'}
          },
          'width >= 768 && height >= 500': {
            layout: {type: 'hbox', align: 'stretch'}
          }
        },
        items: [
          {
            xtype: 'datefield',
            flex: 1,
            minWidth: 0,
            labelAlign: 'top',
            padding: '0 5 0 0',
            yasmineGuiDate: 'long',
            fieldLabel: 'Effective Start Date',
            stationXmlRelativePath: 'BeginEffectiveTime',
            bind: '{beginEffectiveTime}',
            allowBlank: true
          },
          {
            xtype: 'datefield',
            flex: 1,
            minWidth: 0,
            labelAlign: 'top',
            padding: '0 0 0 5',
            yasmineGuiDate: 'long',
            fieldLabel: 'Effective End Date',
            stationXmlRelativePath: 'EndEffectiveTime',
            bind: '{endEffectiveTime}',
            allowBlank: true
          }
        ]
      },
      {
        xtype: 'person-list',
        margin: '20 0 10 0',
        flex: 1,
        minHeight: 160,
        minWidth: 0,
        reference: 'person-list'
      }
    ],
    buttons: [{
      text: 'Save',
      minWidth: 0,
      iconCls: 'x-fa fa-floppy-o',
      cls: 'yasmine-primary-action',
      handler: 'onSaveClick'
    }, {
      text: 'Cancel',
      minWidth: 0,
      iconCls: 'x-fa fa-ban',
      handler: 'onCancelClick'
    }]
  }
});

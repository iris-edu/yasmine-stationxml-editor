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


Ext.define('yasmine.view.xml.builder.parameter.components.person.PersonEdit', {
  extend: 'Ext.window.Window',
  xtype: 'person-edit',
  requires: [
    'yasmine.view.xml.builder.parameter.components.person.PersonEditModel',
    'yasmine.view.xml.builder.parameter.components.person.PersonEditController'
  ],
  controller: 'person-edit',
  viewModel: 'person-edit',
  title: 'Person',
  modal: true,
  frame: true,
  items: {
    xtype: 'tabpanel',
    height: 400,
    width: 700,
    defaults: {
      xtype: 'grid',
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
      selModel: 'rowmodel'
    },
    items: [
      {
        reference: 'namegrid',
        title: 'Names',
        bind: { store: '{nameStore}', selection: '{selectedNameRow}' },
        columns: [
          {
            text: 'Name',
            dataIndex: '_name',
            flex: 1,
            editor: {
              xtype: 'textfield',
              allowBlank: false
            }
          }],
        tbar: [
          { tooltip: 'Add Name', iconCls: 'x-fa fa-plus', handler: 'onAddNameClick' },
          { tooltip: 'Delete Name', iconCls: 'x-fa fa-minus', handler: 'onDeleteNameClick', disabled: true, bind: { disabled: '{!selectedNameRow}' } },
          { tooltip: 'Edit Name', iconCls: 'x-fa fa-pencil', handler: 'onEditNameClick', disabled: true, bind: { disabled: '{!selectedNameRow}' } }
        ]
      },
      {
        reference: 'agencygrid',
        title: 'Agencies',
        bind: { store: '{agencyStore}', selection: '{selectedAgencyRow}' },
        columns: [
          {
            text: 'Agency',
            dataIndex: '_name',
            flex: 1,
            editor: {
              xtype: 'combobox',
              allowBlank: false,
              queryMode: 'local',
              bind: {
                store: '{agencyHelpStore}',
                value: '{value}'
              },
              displayField: 'searchText',
              valueField: 'acromyn',
              tpl: Ext.create('Ext.XTemplate',
                '<ul class="x-list-plain"><tpl for="."><li role="option" class="x-boundlist-item">',
                '<b>{acromyn}</b><br/>',
                '<div style="line-height: 120%;">{name}</div>',
                '<div style="line-height: 120%;">{website}</div></li>',
                '<hr>',
                '</tpl></ul>'
              ),
              displayTpl: Ext.create('Ext.XTemplate',
                '<tpl for=".">',
                '{acromyn}',
                '</tpl>'
              ),
              listeners: {
                beforequery: function (record) {
                  record.query = new RegExp(record.query, 'ig');
                }
              }
            }
          }],
        tbar: [
          { tooltip: 'Add Agency', iconCls: 'x-fa fa-plus', handler: 'onAddAgencyClick' },
          { tooltip: 'Delete Agency', iconCls: 'x-fa fa-minus', handler: 'onDeleteAgencyClick', disabled: true, bind: { disabled: '{!selectedAgencyRow}' } },
          { tooltip: 'Edit Agency', iconCls: 'x-fa fa-pencil', handler: 'onEditAgencyClick', disabled: true, bind: { disabled: '{!selectedAgencyRow}' } }
        ]
      },
      {
        reference: 'emailgrid',
        title: 'Emails',
        bind: { store: '{emailStore}', selection: '{selectedEmailRow}' },
        columns: [
          {
            text: 'Email',
            dataIndex: '_email',
            flex: 1,
            editor: {
              xtype: 'textfield',
              vtype: 'email',
              allowBlank: false
            }
          }
        ],
        tbar: [
          { tooltip: 'Add Email', iconCls: 'x-fa fa-plus', handler: 'onAddEmailClick' },
          { tooltip: 'Delete Email', iconCls: 'x-fa fa-minus', handler: 'onDeleteEmailClick', disabled: true, bind: { disabled: '{!selectedEmailRow}' } },
          { tooltip: 'Edit Email', iconCls: 'x-fa fa-pencil', handler: 'onEditEmailClick', disabled: true, bind: { disabled: '{!selectedEmailRow}' } }
        ]
      },
      {
        reference: 'phonegrid',
        title: 'Phones',
        bind: { store: '{phoneStore}', selection: '{selectedPhoneRow}' },
        columns: [
          { text: 'Country Code', dataIndex: '_country_code', width: 110, editor: 'numberfield' },
          { text: 'Area Code', dataIndex: '_area_code', width: 90, editor: 'numberfield' },
          {
            text: 'Phone Number',
            dataIndex: '_phone_number',
            flex: 1,
            editor: {
              xtype: 'textfield',
              allowBlank: false,
              vtype: 'phoneNumber'
            }
          },
          {
            text: 'Description',
            dataIndex: '_description',
            flex: 1,
            editor: {
              xtype: 'textfield',
              allowBlank: false
            }
          }
        ],
        tbar: [
          { tooltip: 'Add Phone', iconCls: 'x-fa fa-plus', handler: 'onAddPhoneClick' },
          { tooltip: 'Delete Phone', iconCls: 'x-fa fa-minus', handler: 'onDeletePhoneClick', disabled: true, bind: { disabled: '{!selectedPhoneRow}' } },
          { tooltip: 'Edit Phone', iconCls: 'x-fa fa-pencil', handler: 'onEditPhoneClick', disabled: true, bind: { disabled: '{!selectedPhoneRow}' } }
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

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


Ext.define('yasmine.view.xml.builder.parameter.components.person.PersonEdit', {
  extend: 'Ext.window.Window',
  xtype: 'person-edit',
  requires: [
    'yasmine.view.xml.builder.parameter.components.person.PersonEditModel',
    'yasmine.view.xml.builder.parameter.components.person.PersonEditController'
  ],
  controller: 'person-edit',
  viewModel: 'person-edit',
  bind: {
    title: '{personLabel}'
  },
  modal: true,
  frame: false,
  cls: 'yasmine-window yasmine-collection-window',
  layout: 'fit',
  minWidth: 280,
  tools: [{
    type: 'help',
    handler: 'onHelpClick'
  }],
  listeners: {
    show: function () {
      var viewModel = this.getViewModel();
      viewModel.notify();
      this.setTitle(viewModel.get('personLabel'));
      yasmine.utils.ResponsiveUtil.fitWindow(this, {
        minWidth: 700,
        minHeight: 400,
        width: 720,
        height: 480
      });
    },
    resize: function () {
      yasmine.utils.ResponsiveUtil.clampWindow(this);
    }
  },
  items: {
    xtype: 'tabpanel',
    tabBar: {
      ui: 'sheet'
    },
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
              allowBlank: false,
              listeners: {
                specialkey: function (field, e) {
                  if (e.getKey() === e.ENTER) {
                    e.preventDefault();
                    var rowEditor = field.up('roweditor');
                    if (rowEditor && rowEditor.completeEdit) {
                      rowEditor.completeEdit();
                    }
                  }
                }
              }
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
              allowBlank: false,
              regex: /^[A-Za-z0-9_.-]+@[A-Za-z0-9_.-]+$/,
              regexText: 'Email must match the StationXML email pattern.'
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
          {
            text: 'Country Code',
            dataIndex: '_country_code',
            flex: 1,
            minWidth: 72,
            editor: {
              xtype: 'textfield',
              vtype: 'countryCode',
              allowBlank: true
            }
          },
          {
            text: 'Area Code',
            dataIndex: '_area_code',
            flex: 1,
            minWidth: 72,
            editor: {
              xtype: 'textfield',
              vtype: 'areaCode',
              allowBlank: false
            }
          },
          {
            text: 'Phone Number',
            dataIndex: '_phone_number',
            flex: 1,
            editor: {
              xtype: 'textfield',
              allowBlank: false,
              vtype: 'phoneNumber',
              listeners: {
                change: function (field, newValue) {
                  if (field.phoneFormatting) {
                    return;
                  }
                  var formatted = Ext.form.field.VTypes.phoneNumberFormat(newValue);
                  if (formatted === newValue) {
                    return;
                  }
                  var input = field.inputEl && field.inputEl.dom;
                  var caret = input ? input.selectionStart : null;
                  field.phoneFormatting = true;
                  field.setValue(formatted);
                  field.phoneFormatting = false;
                  if (input && caret != null) {
                    var next = caret + (String(formatted).length - String(newValue).length);
                    if (next < 0) {
                      next = 0;
                    }
                    if (next > formatted.length) {
                      next = formatted.length;
                    }
                    input.setSelectionRange(next, next);
                  }
                }
              }
            }
          },
          {
            text: 'Description',
            dataIndex: '_description',
            flex: 1,
            editor: {
              xtype: 'textfield',
              allowBlank: true
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

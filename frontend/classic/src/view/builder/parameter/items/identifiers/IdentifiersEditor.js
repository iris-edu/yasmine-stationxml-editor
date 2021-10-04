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


Ext.define('yasmine.view.xml.builder.parameter.items.identifiers.IdentifiersEditor', {
  extend: 'Ext.form.Panel',
  xtype: 'yasmine-identifiers-field',
  requires: [
    'yasmine.view.xml.builder.parameter.items.identifiers.IdentifiersEditorModel',
    'yasmine.view.xml.builder.parameter.items.identifiers.IdentifiersEditorController'
  ],
  viewModel: 'identifiers-editor',
  controller: 'identifiers-editor',
  border: true,
  items: [
    {
      bind: {
        html: '{validationErrors}',
        hidden: '{!canShowValidationError}'
      },
      hidden: true,
      width: '100%',
      padding: '5 8 5 8'
    },
    {
      xtype: 'grid',
      flex: 1,
      width: 400,
      height: 300,
      reference: 'identifiergrid',
      plugins: [{
        ptype: 'rowediting',
        clicksToMoveEditor: 1,
        listeners: {
          canceledit: 'onCancelEditing'
        }
      }],
      selModel: 'rowmodel',
      bind: {
        store: '{identifierStore}',
        selection: '{identifierSelectedRow}'
      },
      columns: [
        {
          header: 'Identifier',
          dataIndex: 'value',
          flex: 1,
          editor: {
            completeOnEnter: true,
            field: {
              xtype: 'combobox',
              allowBlank: false,
              queryMode: 'local',
              bind: {
                store: '{identifierHelpStore}',
                value: '{value}'
              },
              validator: function (value) {
                let result = yasmine.utils.ValidatorUtil.validate(yasmine.NodeTypeEnum.network, 'source_id', value, true);
                return (result.message && result.message.length > 0) ? result.message.join() : true;
              },
              displayField: 'searchText',
              valueField: 'value',
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
              listConfig: {
                listeners: {
                  beforeshow: function (picker) {
                    picker.minWidth = 600;
                  }
                }
              },
              listeners: {
                beforequery: function (record) {
                  record.query = new RegExp(record.query, 'ig');
                }
              }
            },
          }
        }
      ],
      tbar: [
        {
          xtype: 'button',
          iconCls: 'x-fa fa-plus',
          tooltip: 'Create Identifier',
          handler: 'onAddClick'
        },
        {
          xtype: 'button',
          iconCls: 'x-fa fa-minus',
          tooltip: 'Delete Identifier',
          handler: 'onDeleteClick',
          disabled: true,
          bind: {
            disabled: '{!identifierSelectedRow}'
          }
        },
        {
          iconCls: 'x-fa fa-pencil',
          tooltip: 'Edit Identifier',
          handler: 'onEditClick',
          disabled: true,
          bind: {
            disabled: '{!identifierSelectedRow}'
          }
        }
      ]
    }
  ]
});

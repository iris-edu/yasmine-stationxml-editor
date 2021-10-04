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


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.ValueEditor', {
  extend: 'Ext.grid.Panel',
  xtype: 'channel-response-value-editor',
  requires: [
    'Ext.grid.column.Action'
  ],
  hideHeaders: true,
  bind: {
    store: '{valueStore}',
    title: '\'{nodeName}\' node',
    emptyText: 'The \'<b>{nodeName}</b>\' node doesn\'t have value',
  },
  viewModel: {
    data: {
      nodeName: ''
    },
    stores: {
      valueStore: {
        data: []
      }
    }
  },
  controller: {
    id: 'channel-response-value-editor-controller',
    setNodeName: function (nodeName) {
      this.getViewModel().set('nodeName', nodeName);
    },
    setRecord: function (name, value, canHaveValue) {
      let store = this.getView().getStore();
      if (store.count() > 0) {
        store.removeAll(true);
      }
      store.add(Ext.create('XmlValue', {name: name, value: value, canHaveValue: canHaveValue}));
      store.commitChanges();
    },
    onRowEdit: function (e, data) {
      if (!data.record.dirty) {
        return
      }

      this.getView().getStore().commitChanges();
      this.fireEvent(`onNode${data.field}Updated`, data.record);
    },
    onRowCancelEdit: function () {
      this.getView().getStore().rejectChanges()
    }
  },
  plugins: [{
    ptype: 'cellediting',
    clicksToMoveEditor: 1,
    clicksToEdit: 1,
    listeners: {
      canceledit: 'onRowCancelEdit',
      edit: 'onRowEdit'
    }
  }],
  columns: [
    {
      text: 'Name',
      dataIndex: 'name',
      flex: 1,
      renderer: function (val) {
        return `Name: <span data-qtip="Node Name"><b>${val}</b></span>`;
      },
      editor: {
        allowBlank: false
      }
    },
    {
      text: 'Value',
      dataIndex: 'value',
      flex: 1,
      renderer: function (val, record) {
        if (!record.record.get('canHaveValue')) {
          return 'Value: <span data-qtip="Value is allowed only if the node doesn\'t have children" style="color: #e2000c">Not allowed</span>'
        }
        let value = (val) ? val : 'N/A';
        return `Value: <span data-qtip="Node Value"><b>${value}</b></span>`;
      },
      getEditor: function (record) {
        if (!record) {
          return false;
        }

        if (!record.get('canHaveValue')) {
          return false;
        }

        return Ext.create('Ext.grid.CellEditor', {
          field: Ext.create('Ext.form.field.Text', {
            allowBlank: true
          })
        });
      }
    }
  ]

});

Ext.define('XmlValue', {
  extend: 'Ext.data.Model',
  fields: [
    'name',
    'value',
    'canHaveValue'
  ]
});

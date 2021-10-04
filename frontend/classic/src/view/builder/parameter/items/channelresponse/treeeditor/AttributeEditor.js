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


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.AttributeEditor', {
  extend: 'Ext.grid.Panel',
  xtype: 'channel-response-attribute-editor',
  requires: [
    'Ext.grid.column.Action'
  ],
  bind: {
    title: '\'{nodeName}\' node attributes',
    emptyText: 'The \'<b>{nodeName}</b>\' node doesn\'t have attributes'
  },
  hideHeaders: true,
  viewModel: {
    data: {
      nodeName: ''
    }
  },
  controller: {
    id: 'channel-response-attribute-editor-controller',
    setNodeName: function (nodeName) {
      this.getViewModel().set('nodeName', nodeName);
    },
    addRecord: function (name, value) {
      let store = this.getView().getStore();
      store.add(Ext.create('XmlAttribute', {name: name, value: value}));
      store.commitChanges();
    },
    onAddClick: function () {
      let view = this.getView();
      let record = Ext.create('XmlAttribute', {name: '', value: ''});
      view.store.insert(0, record);

      let rowEditing = view.findPlugin('rowediting');
      rowEditing.startEdit(record);
    },
    onRemoveClick: function (view, recIndex, cellIndex, item, e, record) {
      let nodeName = this.getViewModel().get('nodeName');
      Ext.MessageBox.show({
        title: `Delete '<b>${record.get('name')}</b>' attribute`,
        msg: `Are you sure you want to delete '<b>${record.get('name')}</b>' attribute of '<b>${nodeName}</b>' node?`,
        buttons: Ext.MessageBox.YESNO,
        buttonText: {
          yes: "Delete",
          no: "Cancel"
        },
        icon: Ext.MessageBox['QUESTION'],
        scope: this,
        fn: function (btn) {
          if (btn === 'yes') {
            record.drop();
            this.getView().getStore().commitChanges();
            this.fireEvent('onAttributeDeleted', record);
          }
        }
      });
    },
    onRowEdit: function (e, data) {
      if (!data.record.dirty) {
        return
      }

      let store = this.getView().getStore();
      store.commitChanges();

      let result = store.getData().items.map(x => {
        return {name: x.get('name'), value: x.get('value')}
      });
      this.fireEvent('onAttributeUpdated', result);
    },
    onRowCancelEdit: function () {
      this.getView().getStore().rejectChanges()
    }
  },
  plugins: [{
    ptype: 'rowediting',
    clicksToMoveEditor: 1,
    clicksToEdit: 1,
    listeners: {
      canceledit: 'onRowCancelEdit',
      edit: 'onRowEdit'
    }
  }],
  store: {
    data: []
  },
  columns: [
    {
      text: 'Name',
      dataIndex: 'name',
      flex: 1,
      renderer: function (val) {
        return `Name: <span data-qtip="Attribute name"><b>${val}</b></span>`;
      },
      editor: {
        allowBlank: false
      }
    },
    {
      text: 'Value',
      dataIndex: 'value',
      flex: 1,
      renderer: function (val) {
        return `Value: <span data-qtip="Attribute value"><b>${val}</b></span>`;
      },
      editor: {
        allowBlank: false
      }
    },
    {
      menuDisabled: true,
      sortable: false,
      xtype: 'actioncolumn',
      align: 'center',
      width: 45,
      items: [
        {
          iconCls: 'x-fa fa-minus-circle',
          tooltip: 'Delete Attribute',
          handler: 'onRemoveClick'
        }
      ]
    }
  ],
  tools: [
    {
      bind: {
        tooltip: 'Add a new attribute to \'{nodeName}\' node'
      },
      type: 'plus',
      handler: 'onAddClick'
    }
  ]

});

Ext.define('XmlAttribute', {
  extend: 'Ext.data.Model',
  fields: [
    'name',
    'value'
  ]
});

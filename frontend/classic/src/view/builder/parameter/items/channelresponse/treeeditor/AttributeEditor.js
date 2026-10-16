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
* 2026-09-30, version 4.4.0-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.AttributeEditor', {
  extend: 'Ext.grid.Panel',
  xtype: 'channel-response-attribute-editor',
  requires: [
    'Ext.grid.column.Action',
    'yasmine.utils.StationXmlHelpContext',
    'yasmine.view.xml.builder.parameter.items.float.StationXmlDoubleField'
  ],
  bind: {
    title: '\'{nodeName}\' node attributes',
    emptyText: 'The \'<b>{nodeName}</b>\' node doesn\'t have attributes'
  },
  hideHeaders: true,
  listeners: {
    selectionchange: function (selectionModel, records) {
      var record = records && records[0];
      var grid = selectionModel.view && selectionModel.view.up('grid');
      var controller = grid && grid.getController();
      var parameterEditor = grid && grid.up('parameter-editor');
      if (!record || !controller || !controller.selectedNode ||
          !parameterEditor) {
        return;
      }
      parameterEditor.stationXmlHelpContext =
        yasmine.utils.StationXmlHelpContext.buildResponsePath(
          controller.selectedNode,
          '/FDSNStationXML/Network/Station/Channel/Response',
          record.get('name')
        );
    }
  },
  viewModel: {
    data: {
      nodeName: ''
    }
  },
  controller: {
    id: 'channel-response-attribute-editor-controller',
    selectedNode: null,
    nodeDefinition: null,
    nodeReadOnly: true,
    setNode: function (node, definition, readOnly) {
      this.selectedNode = node;
      this.nodeDefinition = definition;
      this.nodeReadOnly = readOnly;
      this.getViewModel().set('nodeName', node ? node.get('key') : '');
    },
    addRecord: function (name, value, definition, readOnly) {
      let store = this.getView().getStore();
      if (!store || store.isEmptyStore) {
        store = Ext.create('Ext.data.Store', {
          model: 'XmlAttribute',
          data: []
        });
        this.getView().setStore(store);
      }
      store.add(Ext.create('XmlAttribute', {
        name: name,
        value: value,
        definition: definition,
        readOnly: readOnly
      }));
      store.commitChanges();
    },
    onAddClick: function () {
      let options = yasmine.utils.ResponseSchemaUtil.allowedAttributes(this.selectedNode);
      if (!options.length) {
        Ext.toast('No StationXML attributes are available for this node.');
        return;
      }
      let menu = Ext.create('Ext.menu.Menu');
      Ext.Array.each(options, function (option) {
        menu.add({
          text: Ext.htmlEncode(option.name),
          handler: function () {
            this.addSchemaAttribute(option);
            menu.destroy();
          },
          scope: this
        });
      }, this);
      menu.showBy(this.getView().getHeader());
    },
    addSchemaAttribute: function (option) {
      let definition = option.definition || {};
      let value = definition.fixed !== undefined
        ? definition.fixed
        : yasmine.utils.ResponseSchemaUtil.defaultScalarValue(definition.type);
      let record = Ext.create('XmlAttribute', {
        name: option.name,
        value: value,
        definition: definition,
        readOnly: false
      });
      this.getView().getStore().insert(0, record);
      this.publishAttributes();
      if (definition.fixed === undefined) {
        let valueColumn = this.getView().getColumnManager().getHeaderByDataIndex('value');
        this.getView().findPlugin('cellediting').startEdit(record, valueColumn);
      }
    },
    onRemoveClick: function (view, recIndex, cellIndex, item, e, record) {
      let definition = record.get('definition') || {};
      if (record.get('readOnly') || definition.required) {
        return;
      }
      let nodeName = this.getViewModel().get('nodeName');
      Ext.MessageBox.show({
        title: "Delete '<b>" + Ext.String.htmlEncode(record.get('name') || '') + "</b>' attribute",
        msg: "Are you sure you want to delete '<b>" + Ext.String.htmlEncode(record.get('name') || '') +
          "</b>' attribute of '<b>" + Ext.String.htmlEncode(nodeName || '') + "</b>' node?",
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
    onBeforeEdit: function (editor, context) {
      let definition = context.record.get('definition') || {};
      return !context.record.get('readOnly') && definition.fixed === undefined;
    },
    onRowEdit: function (e, data) {
      if (!data.record.dirty) {
        return
      }

      this.publishAttributes();
    },
    publishAttributes: function () {
      let store = this.getView().getStore();
      store.commitChanges();
      let result = store.getData().items.map(function (item) {
        return {name: item.get('name'), value: item.get('value')};
      });
      this.fireEvent('onAttributeUpdated', result);
    },
    typedEditor: function (record) {
      let attributeDefinition = record ? (record.get('definition') || {}) : {};
      if (!record || record.get('readOnly') || attributeDefinition.fixed !== undefined) {
        return false;
      }
      let typeDefinition = yasmine.utils.ResponseSchemaUtil.getType(attributeDefinition.type) || {};
      let field;
      if (typeDefinition.enum && typeDefinition.enum.length) {
        field = Ext.create('Ext.form.field.ComboBox', {
          store: typeDefinition.enum,
          queryMode: 'local',
          forceSelection: true,
          editable: false,
          allowBlank: false
        });
      } else if (typeDefinition.valueType === 'integer') {
        field = Ext.create('Ext.form.field.Number', {
          allowBlank: false,
          allowDecimals: false,
          minValue: typeDefinition.minimum,
          maxValue: typeDefinition.maximum
        });
      } else if (typeDefinition.valueType === 'number') {
        field = Ext.create({
          xtype: 'yasmine-stationxml-double-field',
          allowBlank: false,
          minValue: typeDefinition.minimum,
          maxValue: typeDefinition.maximum
        });
      } else {
        field = Ext.create('Ext.form.field.Text', {allowBlank: true});
      }
      return Ext.create('Ext.grid.CellEditor', {field: field});
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
      beforeedit: 'onBeforeEdit',
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
        return `Name: <span data-qtip="StationXML attribute"><b>${Ext.htmlEncode(val)}</b></span>`;
      }
    },
    {
      text: 'Value',
      dataIndex: 'value',
      flex: 1,
      renderer: function (val, meta, record) {
        let definition = record.get('definition') || {};
        let tip = record.get('readOnly')
          ? 'Foreign or unsupported attributes are read-only'
          : (definition.fixed !== undefined
            ? 'Fixed StationXML attribute value'
            : 'Click to edit');
        return `Value: <span data-qtip="${tip}"><b>${Ext.htmlEncode(String(val))}</b></span>`;
      },
      getEditor: function (record) {
        let grid = this.up('grid');
        return grid.getController().typedEditor(record);
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
          handler: 'onRemoveClick',
          isActionDisabled: function (view, rowIndex, colIndex, item, record) {
            let definition = record.get('definition') || {};
            return record.get('readOnly') || !!definition.required;
          }
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
  extend: 'yasmine.model.CollectionItem',
  fields: [
    'name',
    'value',
    'definition',
    'readOnly'
  ]
});

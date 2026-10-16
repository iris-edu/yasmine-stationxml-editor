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
* 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.parameter.items.identifiers.IdentifiersEditorController', {
  extend: 'yasmine.view.xml.builder.parameter.ParameterItemEditorController',
  alias: 'controller.identifiers-editor',
  initData: function () {
    let record = this.getViewModel().get('record');
    if (record.get('value')) {
      let store = this.getViewModel().getStore('identifierStore');
      let values = Ext.isArray(record.get('value')) ?
        record.get('value') : [record.get('value')];
      values.forEach(function (value) {
        let identifier = new yasmine.view.xml.builder.parameter.items.identifiers.Identifier();
        let structured = value && typeof value === 'object';
        identifier.set({
          type: structured ? (value.type || '') : '',
          value: structured ? value.value : value,
          legacy: !structured
        });
        identifier.phantom = false;
        identifier.modified = {};
        store.add(identifier);
      })
    }
  },
  fillRecord: function () {
    let record = this.getViewModel().get('record');
    let store = this.getViewModel().getStore('identifierStore');
    let values = store.getData().items.map(function (item) {
      let type = item.get('type');
      let value = item.get('value');
      if (item.get('legacy') && !type) {
        return value;
      }
      return {
        type: type || null,
        value: value
      };
    });

    record.set('value', values);
  },
  validate: function () {
    let errors = [];
    this.getViewModel().getStore('identifierStore').each(function (identifier, index) {
      if (!Ext.String.trim(identifier.get('value') || '')) {
        errors.push('Identifier ' + (index + 1) + ' requires a value.');
      }
    });
    this.getViewModel().set('validation.activeErrors', errors);
    if (errors.length) {
      return false;
    }
    return this.callParent(arguments);
  },
  onAddClick: function () {
    let record = new yasmine.view.xml.builder.parameter.items.identifiers.Identifier();
    let store = this.getViewModel().getStore('identifierStore');
    store.insert(0, record);

    let grid = this.lookupReference('identifiergrid');
    grid.findPlugin('rowediting').startEdit(record, 0);
  },
  onDeleteClick: function () {
    Ext.MessageBox.confirm('Confirm', `Are you sure you want to delete?`, function (btn) {
      if (btn === 'yes') {
        this.getSelectedRecord().drop();
      }
    }, this);
  },
  onEditClick: function () {
    let grid = this.lookupReference('identifiergrid');
    grid.findPlugin('rowediting').startEdit(this.getSelectedRecord(), 0);
  },
  onCancelEditing: function (grid, context) {
    let record = context.record;
    if (record.phantom) {
      let store = this.getViewModel().getStore('identifierStore');
      store.remove(record);
    }
  },
  getSelectedRecord: function () {
    return this.getViewModel().get('identifierSelectedRow');
  }
});

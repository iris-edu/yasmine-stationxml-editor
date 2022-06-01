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


Ext.define('yasmine.view.xml.builder.parameter.items.operators.OperatorsEditorController', {
  extend: 'yasmine.view.xml.builder.parameter.ParameterItemEditorController',
  alias: 'controller.operators-editor',
  listen: {
    controller: {
      '#operators-editor-form-controller': {
        operatorUpdated: 'onOperatorUpdated'
      }
    }
  },
  initData: function () {
    let value = this.getViewModel().get('record').get('value');
    if (!value) {
      return;
    }

    let store = this.getViewModel().getStore('operatorStore');
    value.forEach(function (item) {
      let operator = new yasmine.view.xml.builder.parameter.items.operators.Operator();
      operator.set('website', item.website)
      operator.set('agency', item.agency)
      operator.set('contacts', item.contacts)
      operator.modified = {};
      store.insert(0, operator);
    });
  },
  fillRecord: function () {
    let record = this.getViewModel().get('record');
    let operators = this.getViewModel().getStore('operatorStore').getData().items.map(function (item) {
      let data = item.getData();
      return {
        'py/object': 'obspy.core.inventory.util.Operator',
        contacts: data.contacts,
        website: data.website,
        agency: data.agency
      };
    });

    record.set('value', operators);
  },
  onOperatorUpdated: function (record) {
    let store = this.getViewModel().getStore('operatorStore');
    store.insert(0, record);
  },
  onAddClick: function () {
    this.showEditForm(new yasmine.view.xml.builder.parameter.items.operators.Operator());
  },
  onEditClick: function () {
    this.showEditForm(this.getSelectedRecord());
  },
  onDeleteClick: function () {
    Ext.MessageBox.confirm('Confirm', `Are you sure you want to delete?`, function (btn) {
      if (btn === 'yes') {
        this.getSelectedRecord().drop();
      }
    }, this);
  },
  getSelectedRecord: function () {
    return this.getViewModel().get('selectedOperatorRow');
  },
  showEditForm: function (record) {
    let mainRecord = this.getViewModel().get('record');
    let form = Ext.create({ xtype: 'operators-editor-form' });
    form.getViewModel().set('nodeTypeId', mainRecord.get('node_type_id'))
    form.getViewModel().set('parameterId', mainRecord.get('parameterId'))
    form.getController().initData(record);
    form.show();
  }
});

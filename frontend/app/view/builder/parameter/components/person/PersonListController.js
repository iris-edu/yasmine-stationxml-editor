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


Ext.define('yasmine.view.xml.builder.parameter.components.person.PersonListController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.person-list',
  listen: {
    controller: {
      '#person-edit-controller': {
        personUpdated: 'onPersonUpdated'
      }
    }
  },
  initData: function (persons) {
    let store = this.getViewModel().getStore('personStore');
    store.removeAll();

    if (!persons) {
      return;
    }

    persons.forEach(function (item) {
      let record = new yasmine.view.xml.builder.parameter.components.person.Person();
      record.set('_names', []);
      record.set('_agencies', []);
      record.set('_emails', []);
      record.set('_phones', []);
      let names = (item._names) ? item._names : (item.names) ? item.names : null;
      if (names) {
        record.set('_names', names.map(function (item) { return { _name: item }; }));
      }
      let agencies = (item._agencies) ? item._agencies : (item.agencies) ? item.agencies : null;
      if (agencies) {
        record.set('_agencies', agencies.map(function (item) { return { _name: item }; }));
      }
      let emails = (item._emails) ? item._emails : (item.emails) ? item.emails : null;
      if (emails) {
        record.set('_emails', emails.map(function (item) { return { _email: item }; }));
      }
      let phones = (item._phones) ? item._phones : (item.phones) ? item.phones : null;
      if (phones) {
        let records = phones.map(function (item) {
          return {
            'py/object': 'obspy.core.inventory.util.PhoneNumber',
            country_code: item.country_code,
            area_code: item.area_code,
            phone_number: (item._phone_number) ? item._phone_number : (item.phone_number) ? item.phone_number : null,
            description: item.description
          };
        })
        record.set('_phones', records);
      }

      record.modified = {};
      store.insert(0, record);
    });
  },
  onPersonUpdated: function (person) {
    var store = this.getViewModel().getStore('personStore');
    store.insert(0, person);
  },
  onAddClick: function () {
    this.showForm(new yasmine.view.xml.builder.parameter.components.person.Person());
  },
  onDeleteClick: function () {
    Ext.MessageBox.confirm('Confirm', `Are you sure you want to delete?`, function (btn) {
      if (btn === 'yes') {
        this.getSelectedRecord().drop();
      }
    }, this);
  },
  onEditClick: function () {
    this.showForm(this.getSelectedRecord());
  },
  getSelectedRecord: function () {
    return this.getView().getSelection()[0];
  },
  getData: function () {
    return this.getViewModel()
      .getStore('personStore')
      .getData()
      .items
      .map(function (item) {
        return {
          'py/object': 'obspy.core.inventory.util.Person',
          names: item.getData()._names.map(function (item) { return item._name }),
          emails: item.getData()._emails.map(function (item) { return item._email }),
          agencies: item.getData()._agencies.map(function (item) { return item._name }),
          phones: item.getData()._phones.map(function (item) {
            return {
              'py/object': 'obspy.core.inventory.util.PhoneNumber',
              country_code: item._country_code,
              area_code: item._area_code,
              phone_number: item._phone_number,
              description: item._description
            }
          })
        }
      });
  },
  showForm(record) {
    var editor = Ext.create({ xtype: 'person-edit' });
    editor.getViewModel().set('person', record);
    editor.getViewModel().set('nodeTypeId', this.getViewModel().get('nodeTypeId'));
    editor.getViewModel().set('parameterId', this.getViewModel().get('parameterId'));
    editor.getController().initData();
    editor.show();
  }
});

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
* 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
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
  syncPersonChrome: function () {
    var view = this.getView();
    var viewModel = this.getViewModel();
    var toolbar;
    var label;
    var buttons;
    var personLabel;
    if (!view || view.destroyed || !viewModel) {
      return;
    }
    viewModel.notify();
    personLabel = viewModel.get('personLabel') || 'Author';
    toolbar = view.getDockedItems('toolbar[dock=top]')[0];
    if (!toolbar) {
      return;
    }
    label = toolbar.down('#personCollectionLabel');
    if (label && label.setText) {
      label.setText(viewModel.get('personCollectionLabel') || 'Authors');
    }
    buttons = toolbar.query('button');
    Ext.Array.each(['Add ', 'Delete ', 'Edit '], function (prefix, index) {
      if (buttons[index] && buttons[index].setTooltip) {
        buttons[index].setTooltip(prefix + personLabel);
      }
    });
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
        record.set('_names', names.map(function (n) {
          var val = (typeof n === 'string') ? n : (n._name || n.name || '');
          return { _name: val };
        }));
      }
      let agencies = (item._agencies) ? item._agencies : (item.agencies) ? item.agencies : null;
      if (agencies) {
        record.set('_agencies', agencies.map(function (a) {
          var val = (typeof a === 'string') ? a : (a._name || a.name || '');
          return { _name: val };
        }));
      }
      let emails = (item._emails) ? item._emails : (item.emails) ? item.emails : null;
      if (emails) {
        record.set('_emails', emails.map(function (e) {
          var val = (typeof e === 'string') ? e : (e._email || e.email || '');
          return { _email: val };
        }));
      }
      let phones = (item._phones) ? item._phones : (item.phones) ? item.phones : null;
      if (phones) {
        let records = phones.map(function (p) {
          return {
            'py/object': 'obspy.core.inventory.util.PhoneNumber',
            country_code: p._country_code != null ? p._country_code : p.country_code,
            area_code: p._area_code != null ? p._area_code : p.area_code,
            phone_number: p._phone_number != null ? p._phone_number : (p.phone_number != null ? p.phone_number : null),
            description: p._description != null ? p._description : p.description
          };
        });
        record.set('_phones', records);
      }

      record.modified = {};
      if (!store.contains(record)) {
        store.insert(0, record);
      }
    });
  },
  onPersonUpdated: function (person) {
    var store = this.getViewModel().getStore('personStore');
    if (!store.contains(person)) {
      store.insert(0, person);
    }
    var grid = this.getView();
    if (grid && grid.getView()) {
      grid.getView().refresh();
    }
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
        var data = item.getData();
        var names = (data._names || []).map(function (n) {
          return (typeof n === 'string') ? n : (n._name || n.name || '');
        });
        var emails = (data._emails || []).map(function (e) {
          return (typeof e === 'string') ? e : (e._email || e.email || '');
        });
        var agencies = (data._agencies || []).map(function (a) {
          return (typeof a === 'string') ? a : (a._name || a.name || '');
        });
        var phones = (data._phones || []).map(function (p) {
          return {
            'py/object': 'obspy.core.inventory.util.PhoneNumber',
            country_code: p._country_code != null ? p._country_code : p.country_code,
            area_code: p._area_code != null ? p._area_code : p.area_code,
            phone_number: p._phone_number != null ? p._phone_number : p.phone_number,
            description: p._description != null ? p._description : p.description
          };
        });
        return {
          'py/object': 'obspy.core.inventory.util.Person',
          names: names,
          emails: emails,
          agencies: agencies,
          phones: phones
        };
      });
  },
  showForm(record) {
    if (this.personEditor && !this.personEditor.destroyed) {
      this.personEditor.close();
    }
    var editor = Ext.create({ xtype: 'person-edit' });
    this.personEditor = editor;
    editor.getViewModel().set('person', record);
    editor.getViewModel().set('nodeTypeId', this.getViewModel().get('nodeTypeId'));
    editor.getViewModel().set('parameterId', this.getViewModel().get('parameterId'));
    editor.getViewModel().set(
      'stationXmlPersonPath',
      this.getViewModel().get('stationXmlPersonPath') || 'Author'
    );
    editor.getViewModel().set(
      'stationXmlParameterName',
      this.getViewModel().get('stationXmlParameterName') || 'comments'
    );
    editor.getController().initData();
    editor.show();
  }
});

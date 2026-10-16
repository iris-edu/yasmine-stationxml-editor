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


Ext.define('yasmine.view.xml.builder.parameter.components.person.PersonEditController', {
    extend: 'Ext.app.ViewController',
    alias: 'controller.person-edit',
    id: 'person-edit-controller', // Required for event listening
    requires: [
        'yasmine.utils.HelpUtil',
        'yasmine.utils.StationXmlHelpContext'
    ],
    initData: function () {
        var that = this;
        var record = null;
        var person = this.getViewModel().get('person');
        if (person.get('_names')) {
            person.get('_names').forEach(function(item) {
                record = new yasmine.view.xml.builder.parameter.components.person.Name();
                record.set('_name', item._name);
                record.modified = {};
                that.insertRecord('nameStore', record)
            });
        }
        if (person.get('_agencies')) {
            person.get('_agencies').forEach(function(item) {
                record = new yasmine.view.xml.builder.parameter.components.person.Agency();
                record.set('_name', item._name);
                record.modified = {};
                that.insertRecord('agencyStore', record)
            });
        }
        if (person.get('_emails')) {
            person.get('_emails').forEach(function(item) {
                record = new yasmine.view.xml.builder.parameter.components.person.Email();
                record.set('_email', item._email);
                record.modified = {};
                that.insertRecord('emailStore', record)
            });
        }
        if (person.get('_phones')) {
            person.get('_phones').forEach(function(item) {
                record = new yasmine.view.xml.builder.parameter.components.person.Phone();
                record.set('_country_code', item.country_code != null ? String(item.country_code) : null);
                record.set('_area_code', item.area_code != null ? String(item.area_code) : null);
                record.set('_phone_number', Ext.form.field.VTypes.phoneNumberFormat(item.phone_number));
                record.set('_description', item.description);
                record.modified = {};
                that.insertRecord('phoneStore', record)
            });
        }
    },
    onSaveClick: function () {
        if (!this.completeAllRowEdits()) {
            return;
        }
        if (!this.validateData()) {
            return;
        }
        var record = this.getViewModel().get('person');
        record.set('_names', this.getItems('nameStore'));
        record.set('_agencies', this.getItems('agencyStore'));
        record.set('_emails', this.getItems('emailStore'));
        record.set('_phones', this.getItems('phoneStore'));
        record.set('py/object', 'obspy.core.inventory.util.Person');

        this.fireEvent('personUpdated', record);
        this.closeView();
    },
    completeAllRowEdits: function () {
        var gridRefs = ['namegrid', 'agencygrid', 'emailgrid', 'phonegrid'];
        for (var i = 0; i < gridRefs.length; i++) {
            var grid = this.lookupReference(gridRefs[i]);
            if (grid) {
                var plugin = grid.findPlugin('rowediting');
                if (plugin && plugin.editing && plugin.context && plugin.context.record) {
                    try {
                        if (plugin.completeEdit() === false) {
                            return false;
                        }
                    } catch (e) {
                        return false;
                    }
                }
            }
        }
        return true;
    },
    validateData: function () {
        var errors = [];
        var integerPattern = /^[+-]?\d+$/;
        var phonePattern = /^[0-9]+-[0-9]+$/;
        var emailPattern = /^[A-Za-z0-9_.-]+@[A-Za-z0-9_.-]+$/;

        this.getViewModel().getStore('emailStore').each(function (email, index) {
            if (!emailPattern.test(email.get('_email') || '')) {
                errors.push('Email ' + (index + 1) +
                    ' does not match the StationXML email pattern.');
            }
        });
        this.getViewModel().getStore('phoneStore').each(function (phone, index) {
            var countryCode = phone.get('_country_code');
            var areaCode = phone.get('_area_code');
            var number = Ext.form.field.VTypes.phoneNumberFormat(phone.get('_phone_number'));
            if (number !== phone.get('_phone_number')) {
                phone.set('_phone_number', number);
            }

            if (countryCode && !integerPattern.test(countryCode)) {
                errors.push('Phone ' + (index + 1) + ' country code must be an integer.');
            }
            if (!areaCode || !integerPattern.test(areaCode)) {
                errors.push('Phone ' + (index + 1) + ' requires an integer area code.');
            }
            if (!number || !phonePattern.test(number)) {
                errors.push('Phone ' + (index + 1) +
                    ' number must contain two digit groups separated by a hyphen.');
            }
        });

        if (errors.length) {
            Ext.Msg.alert('Invalid contact information', errors.join('<br>'));
            return false;
        }
        return true;
    },
    onCancelClick: function () {
        this.closeView();
    },
    onHelpClick: function () {
        var vm = this.getViewModel();
        var tab = this.getView().down('tabpanel');
        var active = tab && tab.getActiveTab();
        var tabPaths = {
            namegrid: 'Name',
            agencygrid: 'Agency',
            emailgrid: 'Email',
            phonegrid: 'Phone'
        };
        var tabPath = active && active.getReference ?
            tabPaths[active.getReference()] : '';
        var personPath = vm.get('stationXmlPersonPath') || 'Author';
        yasmine.utils.HelpUtil.stationXmlHelpMe({
            nodeType: vm.get('nodeTypeId'),
            parameterName: vm.get('stationXmlParameterName') || 'comments',
            relativePath: yasmine.utils.StationXmlHelpContext.joinPath(
                personPath,
                tabPath
            )
        }, vm.get('personLabel') || 'Person');
    },
    onAddNameClick: function () {
        var record = new yasmine.view.xml.builder.parameter.components.person.Name();
        this.insertRecord('nameStore', record)
        this.enableEditing('namegrid', record);
    },
    onAddAgencyClick: function () {
        var record = new yasmine.view.xml.builder.parameter.components.person.Agency();
        this.insertRecord('agencyStore', record)
        this.enableEditing('agencygrid', record);
    },
    onAddEmailClick: function () {
        var record = new yasmine.view.xml.builder.parameter.components.person.Email();
        this.insertRecord('emailStore', record)
        this.enableEditing('emailgrid', record);
    },
    onAddPhoneClick: function () {
        var record = new yasmine.view.xml.builder.parameter.components.person.Phone();
        this.insertRecord('phoneStore', record)
        this.enableEditing('phonegrid', record);
    },
    onDeleteNameClick: function () {
        this.deleteRecord(this.getSelectedNameRecord());
    },
    onDeleteAgencyClick: function () {
        this.deleteRecord(this.getSelectedAgencyRecord());
    },
    onDeleteEmailClick: function () {
        this.deleteRecord(this.getSelectedEmailRecord());
    },
    onDeletePhoneClick: function () {
        this.deleteRecord(this.getSelectedPhoneRecord());
    },
    onEditNameClick: function () {
        this.enableEditing('namegrid', this.getSelectedNameRecord());
    },
    onEditAgencyClick: function () {
        this.enableEditing('agencygrid', this.getSelectedAgencyRecord());
    },
    onEditEmailClick: function () {
        this.enableEditing('emailgrid', this.getSelectedEmailRecord());
    },
    onEditPhoneClick: function () {
        this.enableEditing('phonegrid', this.getSelectedPhoneRecord());
    },
    getSelectedNameRecord: function () {
        return this.getViewModel().get('selectedNameRow');
    },
    getSelectedAgencyRecord: function () {
        return this.getViewModel().get('selectedAgencyRow');
    },
    getSelectedEmailRecord: function () {
        return this.getViewModel().get('selectedEmailRow');
    },
    getSelectedPhoneRecord: function () {
        return this.getViewModel().get('selectedPhoneRow');
    },
    deleteRecord: function (record) {
        Ext.MessageBox.confirm('Confirm', `Are you sure you want to delete?`, function (btn) {
            if (btn === 'yes') { record.drop(); }
        }, this);
    },
    insertRecord: function (storeName, record) {
        var store = this.getViewModel().getStore(storeName);
        store.insert(0, record);
    },
    enableEditing: function (gridReference, record) {
        var grid = this.lookupReference(gridReference);
        grid.findPlugin('rowediting').startEdit(record, 0);
    },
    getItems(storeName) {
        var result = [];
        this.getViewModel().getStore(storeName).getData().items.forEach(function (item) {
            result.push(item.getData ? item.getData() : Ext.apply({}, item.data));
        });
        return result;
    }
});

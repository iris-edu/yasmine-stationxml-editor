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


Ext.define('yasmine.view.xml.builder.parameter.items.externalreferences.ExternalReferencesEditorController', {
    extend: 'yasmine.view.xml.builder.parameter.ParameterItemEditorController',
    alias: 'controller.external-references-editor',
    initData: function () {
        var record = this.getViewModel().get('record');
        if (record.get('value')) {
            var store = this.getViewModel().getStore('dataStore');
            record.get('value').forEach(function (reference) {
                store.add(reference);
            })
        }
    },
    fillRecord: function () {
        var record = this.getViewModel().get('record');
        var references = [];
        var store = this.getViewModel().getStore('dataStore');
        store.getData().items.forEach(function (reference) {
            references.push({
                uri: reference.data.uri,
                description: reference.data.description,
                'py/object': 'obspy.core.inventory.util.ExternalReference'
            });
        })

        record.set('value', references);
    },
    onAddClick: function () {
        var record = new yasmine.view.xml.builder.parameter.items.externalreferences.ExternalReference();
        var store = this.getViewModel().getStore('dataStore');
        store.insert(0, record);

        var grid = this.lookupReference('referencegrid');
        grid.findPlugin('rowediting').startEdit(record, 0);
    },
    onDeleteClick: function () {
        Ext.MessageBox.confirm('Confirm', `Are you sure you want to delete?`, function (btn) {
            if (btn === 'yes') {
                this.getSelectedRecord().drop();
            }
        }, this);
    },
    getSelectedRecord: function () {
        return this.lookupReference('referencegrid').getSelection()[0];
    }
});

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
* 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.XmlImport', {
    extend: 'Ext.window.Window',
    xtype: 'xml-import',
    requires: [
        'Ext.form.Panel',
        'yasmine.view.xml.import.XmlImportController'
    ],
    controller: 'xml-import',
    title: 'Import XML',
    modal: true,
    frame: false,
    cls: 'yasmine-window',
    constrain: true,
    minWidth: 280,
    defaultFocus : 'name',
    listeners: {
        show: function () {
            yasmine.utils.ResponsiveUtil.fitWindow(this, {
                minWidth: 400,
                minHeight: 220,
                width: 480,
                height: 260
            });
        },
        afterlayout: function () {
            yasmine.utils.ResponsiveUtil.clampWindow(this);
        }
    },
    items: {
        xtype: 'form',
        reference: 'importForm',
        width: '100%',
        bodyPadding: 10,
        defaults: {
            anchor: '100%',
            labelWidth: 50
        },
        items: [{
            xtype: 'textfield',
            itemId: 'name',
            name: 'name',
            fieldLabel: 'Name',
            allowBlank: true
        }, {
            xtype: 'filefield',
            emptyText: 'Import an XML',
            fieldLabel: 'XML',
            name: 'xml-path',
            allowBlank: false,
            buttonText: '',
            buttonConfig: {
                iconCls: 'x-fa fa-upload'
            }
        }],
        buttons: [{
            text: 'Upload',
            reference: 'uploadButton',
            iconCls: 'x-fa fa-upload',
            cls: 'yasmine-primary-action',
            handler: 'onImportClick'
        }, {
            text: 'Cancel',
            iconCls: 'x-fa fa-ban',
            handler: 'onCancelClick'
        }]
    }
});

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
* 2026-09-27, version 4.4.0-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.XmlEdit', {
    extend: 'Ext.window.Window',
    xtype: 'xml-edit',
    requires: [
        'Ext.form.Panel',
        'yasmine.view.xml.edit.XmlEditController',
        'yasmine.view.xml.edit.XmlEditModel',
        'Ext.form.field.VTypes',
        'Ext.data.validator.Presence'
    ],
    controller: 'xml-edit',
    viewModel: 'xml-edit',
    bind: {
        title: '{title}'
    },
    modal: true,
    frame: false,
    cls: 'yasmine-window',
    constrain: true,
    layout: {
        type: 'vbox',
        align: 'stretch'
    },
    minWidth: 280,
    defaultFocus: 'name',
    listeners: {
        show: function () {
            yasmine.utils.ResponsiveUtil.fitWindow(this, {
                minWidth: 400,
                minHeight: 400,
                width: 480,
                height: 480
            });
        },
        afterlayout: function () {
            yasmine.utils.ResponsiveUtil.clampWindow(this);
        }
    },
    items: {
        xtype: 'form',
        bodyPadding: 10,
        modelValidation: true,
        defaultType: 'textfield',
        defaults: {
            anchor: '100%',
            listeners: {
                focus: function (field) {
                    var window = field.up('xml-edit');
                    window.stationXmlHelpContext = field.stationXmlRootField ?
                        {rootField: field.stationXmlRootField} :
                        '/FDSNStationXML';
                }
            }
        },
        items: [
            {
                fieldLabel: 'Name',
                bind: '{model.name}',
                name: 'name',
                allowBlank: false,
                allowOnlyWhitespace: false
            },
            {
                xtype: 'displayfield',
                fieldLabel: 'Schema Version',
                bind: '{model.schemaVersion}',
                stationXmlRootField: 'schema_version'
            },
            {
                fieldLabel: 'Source',
                bind: '{model.source}',
                name: 'source',
                allowBlank: true,
                stationXmlRootField: 'source'
            },
            {
                fieldLabel: 'Sender',
                bind: '{model.sender}',
                name: 'sender',
                allowBlank: true,
                stationXmlRootField: 'sender'
            },
            {
                fieldLabel: 'Module',
                bind: '{model.module}',
                name: 'module',
                allowBlank: true,
                stationXmlRootField: 'module'
            },
            {
                fieldLabel: 'Module URI',
                bind: '{model.uri}',
                name: 'uri',
                allowBlank: true,
                stationXmlRootField: 'uri'
            },
            {
                xtype: 'datefield',
                fieldLabel: 'Created (UTC)',
                bind: '{model.created_at}',
                name: 'created_at',
                yasmineGuiDate: 'long',
                allowBlank: false,
                stationXmlRootField: 'created'
            }
        ],
        buttons: [{
            text: 'Save',
            iconCls: 'x-fa fa-floppy-o',
            cls: 'yasmine-primary-action',
            disabled: true,
            formBind: true,
            handler: 'onSaveClick'
        }, {
            text: 'Cancel',
            iconCls: 'x-fa fa-ban',
            handler: 'onCancelClick'
        }]
    },
    tools:[
        {
            type:'help',
            handler: function (event, tool, header) {
                var window = header.up('xml-edit');
                yasmine.utils.HelpUtil.stationXmlHelpMe(
                    window.stationXmlHelpContext || '/FDSNStationXML',
                    'StationXML document'
                );
            }
        }
    ]
});

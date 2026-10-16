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


Ext.define('yasmine.view.xml.import.XmlImportController', {
    extend: 'Ext.app.ViewController',
    id: 'xmlImport-controller',
    alias: 'controller.xml-import',

    onImportClick: function () {
        var form = this.lookupReference('importForm').getForm();
        var that = this;
        var progress;
        var upload = this.lookupReference('uploadButton');
        if (this._importRunning || !form.isValid()) {
            return;
        }
        this._importRunning = true;
        if (upload) {
            upload.setDisabled(true);
        }
        progress = this.startImportProgress(form);
        form.submit({
            url: '/api/xml/ie/',
            timeout: 1800,
            success: function (form, action) {
                var migration = action && action.result && action.result.migration;
                progress.finish(function () {
                    that.fireEvent('xmlImported');
                    that.closeView();
                    that.showMigrationReport(migration);
                });
            },
            failure: function (fp, action) {
                var message = (action && action.result && action.result.message)
                    || 'Only a FDSN StationXML file can be imported';
                that._importRunning = false;
                if (upload) {
                    upload.setDisabled(false);
                }
                progress.stop();
                Ext.Msg.alert('Import XML', message);
            }
        });
    },

    showMigrationReport: function (migration) {
        if (!migration || !Ext.isArray(migration.notes) || !migration.notes.length) {
            return;
        }
        var html = '<p style="margin:0 0 8px 0;">Import finished. Review these StationXML migration notes:</p><ul style="margin:0;padding-left:18px;">';
        migration.notes.forEach(function (note) {
            html += '<li style="margin-bottom:4px;">' + Ext.htmlEncode(note) + '</li>';
        });
        html += '</ul>';
        Ext.Msg.show({
            title: 'Import migration notes',
            message: html,
            buttons: Ext.Msg.OK,
            icon: Ext.Msg.INFO,
            maxWidth: 560
        });
    },

    onCancelClick: function() {
        this.closeView();
    },

    startImportProgress: function (form) {
        var expectedMs = Math.max(15000, (this.importFileBytes(form) / (512 * 1024)) * 1000);
        var started = Ext.now();
        var stopped = false;
        var task;

        Ext.Msg.show({
            title: 'Import XML',
            message: 'Importing StationXML…',
            progress: true,
            progressText: '0%',
            closable: false,
            modal: true,
            minWidth: Ext.Msg.minProgressWidth
        });

        task = Ext.TaskManager.start({
            interval: 250,
            run: function () {
                var elapsed;
                var value;
                if (stopped) {
                    return;
                }
                elapsed = Ext.now() - started;
                value = 0.99 * (1 - Math.exp(-elapsed / expectedMs));
                if (value > 0.99) {
                    value = 0.99;
                }
                Ext.Msg.updateProgress(value, Math.round(value * 100) + '%');
            }
        });

        return {
            stop: function () {
                if (stopped) {
                    return;
                }
                stopped = true;
                Ext.TaskManager.stop(task);
                Ext.Msg.hide();
            },
            finish: function (callback) {
                if (stopped) {
                    return;
                }
                stopped = true;
                Ext.TaskManager.stop(task);
                Ext.Msg.updateProgress(1, '100%');
                Ext.defer(function () {
                    Ext.Msg.hide();
                    if (callback) {
                        callback();
                    }
                }, 400);
            }
        };
    },

    importFileBytes: function (form) {
        var field = form.findField('xml-path');
        var input = field && field.fileInputEl && field.fileInputEl.dom;
        var file = input && input.files && input.files[0];
        return (file && file.size) || 0;
    }

});

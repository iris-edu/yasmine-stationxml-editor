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


Ext.define("yasmine.store.FileLoader", {
    singleton : true,
    load : function(url) {
        Ext.Ajax.request({
            scope: this,
            url: url,
            method: 'GET',
            success: function (response) {
                var contentType = (response.getResponseHeader('content-type') || '').toLowerCase();
                if (contentType.indexOf('json') !== -1) {
                    var blocked = Ext.decode(response.responseText, true) || {};
                    Ext.Msg.alert(
                        'Export blocked',
                        blocked.message || 'StationXML 1.2 validation failed.'
                    );
                    return;
                }
                var disposition = response.getResponseHeader('content-disposition') || '';
                
                var filename = 'download.xml';
                var filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                var matches = filenameRegex.exec(disposition);
                if (matches != null && matches[1]) {
                  filename = matches[1].replace(/['"]/g, '');
                }
                
                var blob = new Blob([response.responseText], { type: 'application/xml' });
                var link = document.createElement('a');
                link.href = window.URL.createObjectURL(blob);
                link.download = filename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            },
            failure: function (response) {
                var payload = Ext.decode(response.responseText, true) || {};
                Ext.Msg.alert(
                    'Export blocked',
                    payload.message || 'Unable to export StationXML.'
                );
            }
        });
    }
});

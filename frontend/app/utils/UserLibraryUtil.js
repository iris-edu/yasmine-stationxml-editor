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


Ext.define("yasmine.utils.UserLibraryUtil", {
  singleton: true,
  importFromUrl: function (url) {
    Ext.Ajax.request({
      scope: this,
      async: false,
      jsonData: { url: url },
      url: `/api/helper/url-user-library/`,
      method: 'POST',
      success: function (response) {
        var result = {};
        try {
          result = JSON.parse(response.responseText || '{}');
        } catch (e) {
          Ext.MessageBox.alert('Error', 'Unable to import user library.');
          return;
        }
        if (result.success) {
          Ext.toast({ html: 'User Library has been imported', align: 't' });
        } else {
          Ext.MessageBox.show({
            title: 'An error occurred',
            msg: result.message,
            buttons: Ext.MessageBox.OK,
            icon: Ext.MessageBox['ERROR']
          });
        }
      },
      failure: function () {
        Ext.MessageBox.alert('Error', 'Unable to import user library.');
      }
    });
  },
  importFromFile: function (form) {
    form.submit({
      url: '/api/helper/zip-user-library/',
      success: function (fp, o) {
        var result = {};
        try {
          result = JSON.parse(o.response.responseText || '{}');
        } catch (e) {
          Ext.MessageBox.alert('Error', 'Unable to import user library.');
          return;
        }
        if (result.success) {
          Ext.toast({ html: 'User Library has been imported', align: 't' });
        } else {
          Ext.MessageBox.alert('Error', result.message || 'Unable to import user library.');
        }
      },
      failure: function (fp, action) {
        var message = (action && action.result && action.result.message) || 'Unable to import user library.';
        Ext.MessageBox.alert('Error', message);
      }
    });
  }
});

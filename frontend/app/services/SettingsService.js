/* ****************************************************************************
* 2026-09-19, version 4.2.0-beta: ASGSR, Alexey Emanov
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
* ****************************************************************************/


Ext.define('yasmine.services.SettingsService', {
  statics: {
    initSettings: function (options) {
      options = options || {};
      return Ext.Ajax.request({
        scope: options.scope || this,
        url: '/api/cfg/0',
        method: 'GET',
        success: function (response) {
          var settings = {};
          try {
            settings = JSON.parse((response && response.responseText) || '{}');
          } catch (e) {
            settings = {};
          }
          yasmine.utils.SettingsUtil.applySettings(settings);
          Ext.GlobalEvents.fireEvent('nrlv2SettingsChanged');
          if (options.success) {
            options.success.call(options.scope || this, settings);
          }
        },
        failure: function (response) {
          if (options.failure) {
            options.failure.call(options.scope || this, response);
          }
        }
      });
    }
  }
});

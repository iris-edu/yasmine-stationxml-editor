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


Ext.define('yasmine.view.settings.SettingsListController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.settings',
  requires: [
    'Ext.window.Toast'
  ],
  init: function () {
    yasmine.view.settings.Settings.load(0, {
      scope: this,
      success: function (record) {
        this.getViewModel().set('settings', record);
        this.getView().loadRecord(record);
      }
    });
  },
  onSaveClick: function () {
    this.getView().updateRecord();
    let record = this.getView().getRecord();
    if (record.dirty) {
      record.save({
        scope: this,
        success: function () {
          this.getViewModel().set('settings', record);
          Ext.toast({ html: 'Settings saved', align: 't' });
          yasmine.services.SettingsService.initSettings();
        }
      });
    } else {
      Ext.toast({ html: 'There is nothing to save', align: 't' });
    }
  },
  importUserLibraryFromUrl: function () {
    let setting = this.getViewModel().get('settings');
    yasmine.utils.UserLibraryUtil.importFromUrl(setting.get('general__user_library_source_url'));
  },
  importUserLibraryFromZip: function () {
    let form = this.lookupReference('importZipForm').getForm();
    if (form.isValid()) {
      yasmine.utils.UserLibraryUtil.importFromFile(form);
    }
  },
  onRequiredFieldDeselect: function (cmp, value) {
    if (value.get('is_critical')) {
      Ext.MessageBox.alert('Error', `The "${value.get('id')}" field cannot be removed. It's mandatory for StationXML`);
      return false;
    }

    return true;
  }
});

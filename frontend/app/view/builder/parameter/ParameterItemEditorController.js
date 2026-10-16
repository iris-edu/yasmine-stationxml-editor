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


Ext.define('yasmine.view.xml.builder.parameter.ParameterItemEditorController', {
  extend: 'Ext.app.ViewController',
  requires: [
    'yasmine.utils.StationXmlHelpContext'
  ],
  lastValidatedValue: undefined,
  lastValidatedResult: undefined,
  validationMessages: function (result) {
    let messages = result && result.message ? result.message : [];
    if ((!result || result.success === false) && messages.length === 0) {
      messages = ['Validation is unavailable.'];
    }
    return messages;
  },
  validate: function () {
    let record = this.getViewModel().get('record');
    let result = this.serverSideValidation(record.get('value'));
    let messages = this.validationMessages(result);
    this.getViewModel().set('validation.activeErrors', messages);
    return !!(result && result.success !== false && messages.length === 0);
  },
  validator: function (value) {
    let result = this.serverSideValidation(value);
    let messages = this.validationMessages(result);
    if (result && result.success && messages.length === 0) {
      return true;
    }
    return messages[0];
  },
  serverSideValidation: function (value) {
    if (value !== this.lastValidatedValue) {
      let record = this.getViewModel().get('record');
      this.lastValidatedValue = value;
      let onlyCritical = record.get('only_critical');
      if (onlyCritical === undefined || onlyCritical === null) {
        onlyCritical = true;
      }
      this.lastValidatedResult = yasmine.utils.ValidatorUtil.validate(
        record.get('node_type_id'),
        record.get('name'),
        value,
        onlyCritical
      );
      if (this.lastValidatedResult && this.lastValidatedResult.message) {
        this.lastValidatedResult.message = yasmine.utils.StationXmlHelpContext.relabelMessages(
          this.lastValidatedResult.message,
          record.get('name'),
          record.get('node_type_id')
        );
      }
    }
    return this.lastValidatedResult;
  }
});

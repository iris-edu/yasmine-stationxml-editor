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


Ext.define('yasmine.view.xml.builder.parameter.ParameterItemEditorController', {
  extend: 'Ext.app.ViewController',
  lastValidatedValue: undefined,
  lastValidatedResult: undefined,
  validate: function () {
    let record = this.getViewModel().get('record');
    let result = this.serverSideValidation(record.get('value'));
    this.getViewModel().set('validation.activeErrors', result.message);
    return !(result.message && result.message.length > 0);
  },
  validator: function (value) {
    let result = this.serverSideValidation(value);
    if (result.success && result.message.length === 0) {
      return true;
    } else {
      return result.message[0];
    }
  },
  serverSideValidation: function (value) {
    if (value !== this.lastValidatedValue) {
      let record = this.getViewModel().get('record');
      this.lastValidatedValue = value;
      this.lastValidatedResult = yasmine.utils.ValidatorUtil.validate(
        record.get('node_type_id'),
        record.get('name'),
        value,
        record.get('only_critical')
      );
    }
    return this.lastValidatedResult;
  }
});

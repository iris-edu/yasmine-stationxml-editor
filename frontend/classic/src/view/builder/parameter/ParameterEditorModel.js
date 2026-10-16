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
* 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.parameter.ParameterEditorModel', {
  extend: 'Ext.app.ViewModel',
  alias: 'viewmodel.parameter-editor',
  requires: [
    'yasmine.utils.StationXmlHelpContext'
  ],
  data: {
    record: null,
    nodeType: null,
    canSave: true,
    showResponseActions: false,
    showEditResponse: false,
    showSelectResponse: false,
    showRecalculateSensitivity: false,
    showImportResp: false
  },
  formulas: {
    title: function (get) {
      var record = get('record');
      if (!record) {
        return 'Edit';
      }
      return `Edit '${yasmine.utils.StationXmlHelpContext.labelForRecord(record)}'`;
    },
    responseEditText: function () {
      return yasmine.utils.ResponsiveUtil.useStackLayout() ? 'Edit' : 'Edit Response';
    },
    responseSelectText: function () {
      return yasmine.utils.ResponsiveUtil.useStackLayout() ? 'Select' : 'Select a new Response';
    },
    responseRecalculateText: function () {
      return 'Recalculate Sensitivity';
    },
    responseImportText: function () {
      return yasmine.utils.ResponsiveUtil.useStackLayout() ? 'RESP' : 'Import RESP';
    }
  }
});

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


Ext.define('yasmine.view.xml.builder.parameter.items.equipments.EquipmentsEditorModel', {
  extend: 'yasmine.view.xml.builder.parameter.ParameterItemEditorModel',
  alias: 'viewmodel.equipments-editor',
  data: {
    selectedEquipment: null
  },
  stores: {
    equipmentsStore: {
      model: 'yasmine.view.xml.builder.parameter.items.equipments.Equipment',
      data: []
    },
    calibrationDateStore: {
      model: 'yasmine.view.xml.builder.parameter.items.equipments.CalibrationDate',
      data: []
    }
  }
});

Ext.define('yasmine.view.xml.builder.parameter.items.equipments.CalibrationDate', {
  extend: 'Ext.data.Model',
  fields: [
    { name: 'value', type: 'date' }
  ]
});

Ext.define('yasmine.view.xml.builder.parameter.items.equipments.Equipment', {
  extend: 'Ext.data.Model',
  fields: [
    {name: 'type', type: 'string'},
    {name: 'description', type: 'string'},
    {name: 'model', type: 'string'},
    {name: 'manufacturer', type: 'string'},
    {name: 'vendor', type: 'string'},
    {name: 'serialNumber', type: 'string'},
    {name: 'resourceId', type: 'string'},
    {name: 'installationDate', type: 'date', dateFormat: yasmine.Globals.DateReadFormat },
    {name: 'removalDate', type: 'date', dateFormat: yasmine.Globals.DateReadFormat },
    {name: 'calibrationDates', type: 'auto' },
    {
      name: 'summary',
      persist: false,
      depends: ['type', 'description', 'model', 'manufacturer', 'vendor', 'serialNumber', 'resourceId'],
      convert: function (value, record) {
        return `
        ${record.get('type')}
        ${record.get('description')}
        ${record.get('model')}
        ${record.get('manufacturer')}
        ${record.get('vendor')}
        ${record.get('serialNumber')}
        ${record.get('resourceId')}
        `;
      }
    }
  ]
});

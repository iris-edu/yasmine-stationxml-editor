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


Ext.define('yasmine.view.xml.builder.parameter.items.equipments.EquipmentsEditorController', {
  extend: 'yasmine.view.xml.builder.parameter.ParameterItemEditorController',
  alias: 'controller.equipments-editor',
  initData: function () {
    let value = this.getViewModel().get('record').get('value');
    if (!value) {
        return;
    }

    let equipmentsStore = this.getViewModel().getStore('equipmentsStore');
    value.forEach(function (equipment) {
      let calibrationDates = [];
      equipment.calibration_dates.forEach(function (date) {
        calibrationDates.push(Ext.Date.parse(date, yasmine.Globals.DateReadFormat, true));
      });

      let equipmentModel = new yasmine.view.xml.builder.parameter.items.equipments.Equipment();
      equipmentModel.set('type', equipment.type);
      equipmentModel.set('description', equipment.description);
      equipmentModel.set('manufacturer', equipment.manufacturer);
      equipmentModel.set('vendor', equipment.vendor);
      equipmentModel.set('serialNumber', equipment.serial_number);
      equipmentModel.set('installationDate', Ext.Date.parse(equipment.installation_date, yasmine.Globals.DateReadFormat, true));
      equipmentModel.set('removalDate', Ext.Date.parse(equipment.removal_date, yasmine.Globals.DateReadFormat, true));
      equipmentModel.set('resourceId', equipment.resource_id);
      equipmentModel.set('model', equipment.model);
      equipmentModel.set('calibrationDates', calibrationDates);
      equipmentsStore.add(equipmentModel);
    });
  },
  fillRecord: function () {
    let equipmentsStore = this.getViewModel().getStore('equipmentsStore');
    let equipments = [];
    equipmentsStore.getData().items.forEach(function (equipment) {
      let calibrationDates = [];
      if (equipment.get('calibrationDates')) {
        equipment.get('calibrationDates').forEach(function (date) {
          calibrationDates.push(Ext.Date.format(date, yasmine.Globals.DateReadFormat));
        });
      }
      equipments.push({
          'py/object': 'obspy.core.inventory.util.Equipment',
          type: equipment.get('type'),
          description: equipment.get('description'),
          manufacturer: equipment.get('manufacturer'),
          vendor: equipment.get('vendor'),
          serial_number: equipment.get('serialNumber'),
          installation_date: Ext.Date.format(equipment.get('installationDate'), yasmine.Globals.DateReadFormat),
          removal_date: Ext.Date.format(equipment.get('removalDate'), yasmine.Globals.DateReadFormat),
          resource_id: equipment.get('resourceId'),
          model: equipment.get('model'),
          calibration_dates: calibrationDates
      });
    });

    this.getViewModel().get('record').set('value', equipments);
  },
  onCalibrationDateCanceled: function (editor, context) {
    let record = context.record;
    if (record.phantom) {
      let store = editor.grid.getStore();
      store.remove(record);
    }
  },
  onCalibrationDateEdited: function (editor, context) {
    let selectedEquipment = this.getViewModel().get('selectedEquipment');
    let calibrationDates = selectedEquipment.get('calibrationDates');
    if (!calibrationDates) {
      calibrationDates = [];
    }

    let record = context.record;
    if (record.previousValues.value) {
      calibrationDates = calibrationDates.filter(function(value){
        return value !== record.previousValues.value;
      });
    }

    calibrationDates.push(record.get('value'));
    selectedEquipment.set('calibrationDates', calibrationDates);
  },
  onDeleteCalibrationDateClick: function (grid, rowIndex) {
    let store = this.getViewModel().getStore('calibrationDateStore');
    let dateToRemove = store.getAt(rowIndex);
    let selectedEquipment = this.getViewModel().get('selectedEquipment');
    let calibrationDates = selectedEquipment.get('calibrationDates');
    let calibrationDateFiltered = calibrationDates.filter(function(value){
      return value !== dateToRemove.get('value');
    });
    selectedEquipment.set('calibrationDates', calibrationDateFiltered);
    dateToRemove.drop();
  },
  onEquipmentSelect: function (grid, record) {
    let dates = record.get('calibrationDates');
    if (!dates) {
      return;
    }
    let store = this.getViewModel().getStore('calibrationDateStore');
    for (const date of dates) {
      let record = new yasmine.view.xml.builder.parameter.items.equipments.CalibrationDate();
      record.set('value', date, {dirty: false});
      store.add(record);
    }
  },
  onEquipmentDeselect: function () {
    let store = this.getViewModel().getStore('calibrationDateStore');
    store.removeAll();
  },
  onAddCalibrationDateClick: function () {
    let record = new yasmine.view.xml.builder.parameter.items.equipments.CalibrationDate();
    record.modified = {};
    let store = this.getViewModel().getStore('calibrationDateStore');
    store.insert(0, record);
    let grid = this.lookup('calibrationdategrid');
    grid.findPlugin('cellediting').startEdit(record, 0);
  },
  onAddEquipmentClick: function () {
    let record = new yasmine.view.xml.builder.parameter.items.equipments.Equipment();
    let store = this.getViewModel().getStore('equipmentsStore');
    store.insert(0, record);
    this.getViewModel().set('selectedEquipment', record);
  },
  onDeleteEquipmentClick: function (grid, rowIndex) {
    let store = this.getViewModel().getStore('equipmentsStore');
    store.getAt(rowIndex).drop();
  },
});

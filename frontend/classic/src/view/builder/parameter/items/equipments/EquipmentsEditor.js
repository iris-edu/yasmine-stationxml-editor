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


Ext.define('yasmine.view.xml.builder.parameter.items.equipments.EquipmentsEditor', {
  extend: 'Ext.form.Panel',
  xtype: 'yasmine-equipments-field',
  requires: [
    'yasmine.view.xml.builder.parameter.items.equipments.EquipmentsEditorModel',
    'yasmine.view.xml.builder.parameter.items.equipments.EquipmentsEditorController',
    'Ext.layout.container.Column'
  ],
  viewModel: 'equipments-editor',
  controller: 'equipments-editor',
  layout: 'hbox',
  items: [
    {
      xtype: 'grid',
      style: 'border: solid #d0d0d0 1px',
      width: 300,
      height: '100%',
      headerBorders: false,
      bind: {
        store: '{equipmentsStore}',
        selection: '{selectedEquipment}'
      },
      tbar: [
        {
          xtype: 'panel',
          html: '<b>Equipments</b>'
        },
        '->',
        {
          tooltip: 'Add Equipment',
          iconCls: 'x-fa fa-plus',
          handler: 'onAddEquipmentClick'
        }
      ],
      actions: {
        delete: {
          iconCls: 'x-fa fa-trash trash-icon-color',
          tooltip: 'Delete Equipment',
          handler: 'onDeleteEquipmentClick'
        },
      },
      listeners: {
        select: 'onEquipmentSelect',
        deselect: 'onEquipmentDeselect',
        // selectionchange: 'onSelectionChange'
      },
      columns: [
        {
          flex: 1,
          dataIndex: 'summary'
        },
        {
          menuDisabled: true,
          sortable: false,
          xtype: 'actioncolumn',
          width: 25,
          items: ['@delete']
        }
      ]
    },
    {
      xtype: 'panel',
      disabled: true,
      padding: '0 0 0 10',
      bind: {
        disabled: '{!selectedEquipment}'
      },
      layout: {
        type: 'column'
      },
      flex: 1,
      defaults: {
        layout: 'form',
        xtype: 'container',
        defaultType: 'textfield',
      },
      items: [
        {
          items: [
            {
              fieldLabel: 'Type',
              bind: '{selectedEquipment.type}',
              itemId: 'focusItem'
            },
            {
              xtype: 'textarea',
              fieldLabel: 'Description',
              bind: '{selectedEquipment.description}'
            },
            {
              fieldLabel: 'Model',
              bind: '{selectedEquipment.model}'
            },
            {
              fieldLabel: 'Manufacturer',
              bind: '{selectedEquipment.manufacturer}'
            },
            {
              fieldLabel: 'Vendor',
              bind: '{selectedEquipment.vendor}'
            },
            {
              fieldLabel: 'Serial Number',
              bind: '{selectedEquipment.serialNumber}'
            },
            {
              fieldLabel: 'Resource Id',
              bind: '{selectedEquipment.resourceId}'
            },
            {
              xtype: 'datefield',
              fieldLabel: 'Installation Date',
              bind: '{selectedEquipment.installationDate}',
              format: yasmine.Globals.DatePrintLongFormat
            },
            {
              xtype: 'datefield',
              fieldLabel: 'Removal Date',
              bind: '{selectedEquipment.removalDate}',
              format: yasmine.Globals.DatePrintLongFormat
            },
          ],
        },
        {
          width: 250,
          items: [
            {
              xtype: 'grid',
              height: 418,
              style: 'border: solid #d0d0d0 1px',
              reference: 'calibrationdategrid',
              plugins: [{
                ptype: 'cellediting',
                clicksToEdit: 1,
                listeners: {
                  canceledit: 'onCalibrationDateCanceled',
                  edit: 'onCalibrationDateEdited'
                }
              }],
              selModel: 'rowmodel',
              bind: {
                store: '{calibrationDateStore}'
              },
              actions: {
                delete: {
                  iconCls: 'x-fa fa-trash trash-icon-color',
                  tooltip: 'Delete Calibration Date',
                  handler: 'onDeleteCalibrationDateClick'
                },
              },
              columns: [
                {
                  xtype: 'datecolumn',
                  flex: 1,
                  editor: {
                    xtype: 'datefield',
                    allowBlank: false,
                    format: yasmine.Globals.DatePrintLongFormat
                  },
                  format: yasmine.Globals.DatePrintLongFormat,
                  dataIndex: 'value'
                },
                {
                  menuDisabled: true,
                  sortable: false,
                  xtype: 'actioncolumn',
                  width: 25,
                  items: ['@delete']
                }
              ],
              tbar: [
                {
                  xtype: 'panel',
                  html: 'Calibration Dates'
                },
                '->',
                {
                  iconCls: 'x-fa fa-plus',
                  tooltip: 'Add Calibration Date',
                  handler: 'onAddCalibrationDateClick'
                }
              ]
            }
          ]
        }
      ]
    }
  ]
});

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


Ext.define('yasmine.view.xml.builder.parameter.items.channelequipment.ChannelEquipmentEditor', {
  extend: 'Ext.form.Panel',
  xtype: 'yasmine-channel-equipment-field',
  requires: [
    'yasmine.view.xml.builder.parameter.items.channelequipment.ChannelEquipmentEditorModel',
    'yasmine.view.xml.builder.parameter.items.channelequipment.ChannelEquipmentEditorController'
  ],
  viewModel: 'channel-equipment-editor',
  controller: 'channel-equipment-editor',
  items: [{
    bind: {
      html: '{validationErrors}',
      hidden: '{!canShowValidationError}'
    },
    hidden: true,
    width: '100%',
    padding: '0 0 0 0'
  }, {
    layout: 'hbox',
    flex: 1,
    items: [{
      layout: {
        type: 'vbox',
        align: 'stretch'
      },
      padding: '0 2 0 0',
      flex: 1,
      items: [{
        xtype: 'textfield',
        fieldLabel: 'Type',
        bind: '{type}',
        itemId: 'focusItem'
      }, {
        xtype: 'textarea',
        fieldLabel: 'Description',
        bind: '{description}'
      }, {
        xtype: 'textfield',
        fieldLabel: 'Model',
        bind: '{model}'
      }, {
        xtype: 'textfield',
        fieldLabel: 'Manufacturer',
        bind: '{manufacturer}'
      }, {
        xtype: 'textfield',
        fieldLabel: 'Vendor',
        bind: '{vendor}'
      }, {
        xtype: 'textfield',
        fieldLabel: 'Serial Number',
        bind: '{serialNumber}'
      }, {
        xtype: 'datefield',
        fieldLabel: 'Installation Date',
        bind: '{installationDate}',
        format: yasmine.Globals.DatePrintLongFormat
      }, {
        xtype: 'datefield',
        fieldLabel: 'Removal Date',
        bind: '{removalDate}',
        format: yasmine.Globals.DatePrintLongFormat
      }, {
        xtype: 'textfield',
        fieldLabel: 'Resource Id',
        bind: '{resourceId}'
      }]
    }, {
      layout: {
        type: 'vbox',
        align: 'stretch'
      },
      flex: 1,
      height: '100%',
      padding: '0 0 0 2',
      items: [{
        xtype: 'grid',
        style: 'border: solid #d0d0d0 1px',
        reference: 'calibrationdategrid',
        width: 200,
        height: '100%',
        plugins: [{
          ptype: 'rowediting'
        }],
        selModel: 'rowmodel',
        bind: {
          store: '{calibrationDateStore}',
          selection: '{selectedCalibrationDateRow}'
        },
        columns: [{
          xtype: 'datecolumn',
          text: 'Calibration Dates',
          flex: 1,
          editor: {
            xtype: 'datefield',
            format: yasmine.Globals.DatePrintLongFormat
          },
          format: yasmine.Globals.DatePrintLongFormat,
          dataIndex: 'value'
        }],
        listeners: {
          itemdblclick: 'onEditClick'
        },
        tbar: [{
          iconCls: 'x-fa fa-plus',
          tooltip: 'Add Calibration Date',
          handler: 'onAddClick'
        }, {
          iconCls: 'x-fa fa-minus',
          tooltip: 'Delete Calibration Date',
          handler: 'onDeleteClick',
          disabled: true,
          bind: {
            disabled: '{!selectedCalibrationDateRow}'
          }
        }, {
          iconCls: 'x-fa fa-pencil',
          tooltip: 'Edit Calibration Date',
          handler: 'onEditClick',
          disabled: true,
          bind: {
            disabled: '{!selectedCalibrationDateRow}'
          }
        }]
      }]
    }]
  }]
});

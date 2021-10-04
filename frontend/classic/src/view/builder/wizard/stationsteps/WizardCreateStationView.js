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
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.wizard.stationsteps.WizardCreateStationView', {
  extend: 'Ext.panel.Panel',
  xtype: 'wizard-create-station',
  controller: {
    initComponent: function () {
      let items = this.lookup('container').items;
      for (let i = 0; i < items.getCount(); i++) {
        let item = items.getAt(i);
        let viewModel = item.getViewModel();
        if (viewModel) {
          viewModel.set('record', new Ext.data.Model({
            name: item.getItemId(),
            value: null,
            only_critical: true,
            node_type_id: yasmine.NodeTypeEnum.station
          }));
        }
      }
    },
    isValid: function () {
      let items = this.lookup('container').items;
      return yasmine.utils.ValidatorUtil.triggerValidation(items);
    },
    fillStoredData: function () {
      let activeRateCmp = this.lookup('instrument_number');
      let stationStoredData = this.getViewModel().get('stationStoredData');
      stationStoredData.activeSampleRate = activeRateCmp.getValue();

      let items = this.lookup('container').items;
      stationStoredData.attributes = [];
      for (let i = 0; i < items.getCount(); i++) {
        let itemViewModel = items.getAt(i).getViewModel();
        if (!itemViewModel) {
          continue;
        }
        let itemRecord = itemViewModel.get('record');
        if (itemRecord.get('value')) {
          stationStoredData.attributes.push(itemRecord);
        }
        if (itemRecord.get('name') === 'code') {
          this.getViewModel().set('stationCode', itemRecord.get('value'));
        }
      }
    }
  },
  layout: 'center',
  items: [
    {
      layout: {
        type: 'vbox',
        align: 'stretch',
        pack: 'start'
      },
      defaults: {
        labelWidth: 150,
      },
      width: 350,
      reference: 'container',
      items: [
        {
          xtype: 'yasmine-text-field',
          itemId: 'code',
          fieldLabel: 'Station Code',
          bind: {
            value: '{record.value}'
          }
        },
        {
          xtype: 'yasmine-date-field',
          itemId: 'start_date',
          fieldLabel: 'Start Date',
          bind: {
            value: '{record.value}'
          }
        },
        {
          xtype: 'yasmine-date-field',
          itemId: 'end_date',
          fieldLabel: 'End Date',
          bind: {
            value: '{record.value}'
          }
        },
        {
          xtype: 'yasmine-latitude-field',
          itemId: 'latitude',
          fieldLabel: 'Latitude',
          bind: {
            value: '{record.value}'
          }
        },
        {
          xtype: 'yasmine-longitude-field',
          itemId: 'longitude',
          fieldLabel: 'Longitude',
          bind: {
            value: '{record.value}'
          }
        },
        {
          xtype: 'yasmine-float-field',
          itemId: 'elevation',
          fieldLabel: 'Elevation',
          bind: {
            value: '{record.value}'
          }
        },
        {
          xtype: 'numberfield',
          reference: 'instrument_number',
          fieldLabel: 'Number of different streams/instruments',
          minValue: 1,
          maxValue: 5,
          value: 1
        },
      ]
    }
  ]
});

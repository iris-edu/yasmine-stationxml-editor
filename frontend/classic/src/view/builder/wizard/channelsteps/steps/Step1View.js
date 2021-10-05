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


Ext.define('yasmine.view.xml.builder.wizard.channelsteps.steps.Step1View', {
  extend: 'Ext.panel.Panel',
  xtype: 'channel-step-1',
  requires: [
    'Ext.ux.Mediator',
    'yasmine.view.xml.builder.parameter.items.text.TextEditor',
    'yasmine.view.xml.builder.parameter.items.date.DateEditor',
  ],
  controller: {
    initComponent: function () {
      let channelInfo = this.getViewModel().get('channelInfo');
      let items = this.getView().items;
      for (let i = 0; i < items.getCount(); i++) {
        let item = items.getAt(i);
        let record = new Ext.data.Model({
          name: item.getItemId(),
          value: channelInfo.get(item.getItemId()),
          only_critical: true,
          node_type_id: yasmine.NodeTypeEnum.channel
        });

        let stationAttributes = this.getViewModel().get('stationAttributes');
        if (stationAttributes.length > 0 && item.getItemId() === 'latitude') {
          record.set('value', this.getStationAttributeValue('latitude'));
        } else if (stationAttributes.length > 0 && item.getItemId() === 'longitude') {
          record.set('value', this.getStationAttributeValue('longitude'));
        } else if (stationAttributes.length > 0 && item.getItemId() === 'elevation') {
          record.set('value', this.getStationAttributeValue('elevation'));
        }
        item.getViewModel().set('record', record);
      }
    },
    isValid: function () {
      let items = this.getView().items;
      let isValid = true;
      for (let i = 0; i < items.getCount(); i++) {
        let item = items.getAt(i);
        if (item.validate && !item.validate()) {
          isValid = false;
        }
      }
      return isValid;
    },
    storeStepData: function () {
      let viewModel = this.getViewModel();
      let channelInfo = viewModel.get('channelInfo');
      let items = this.getView().items;
      for (let i = 0; i < items.getCount(); i++) {
        let item = items.getAt(i);
        if (channelInfo.get(item.getItemId()) !== undefined) {
          channelInfo.set(item.getItemId(), item.getViewModel().get('record').get('value'));
        }
      }
    },
    getStationAttributeValue: function (name) {
      let stationAttributes = this.getViewModel().get('stationAttributes');
      for (let stationAttribute of stationAttributes) {
        if (stationAttribute.get('name') === name) {
          return stationAttribute.get('value');
        }
      }
      return null;
    }
  },
  layout: {
    type: 'vbox',
    align: 'stretch',
    pack: 'start'
  },
  width: 300,
  items: [
    {
      xtype: 'yasmine-text-field',
      itemId: 'location_code',
      fieldLabel: 'Location Code',
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
      xtype: 'yasmine-float-field',
      itemId: 'depth',
      fieldLabel: 'Depth',
      bind: {
        value: '{record.value}'
      }
    }
  ]
});

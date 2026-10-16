/* ****************************************************************************
* 2026-09-27, version 4.4.0-beta: ASGSR, Alexey Emanov
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


Ext.define('yasmine.view.xml.builder.wizard.channelsteps.steps.Step5View', {
  extend: 'Ext.panel.Panel',
  xtype: 'channel-step-5',
  controller: {
    itemIds: ['code1', 'code2', 'code3', 'dip1', 'dip2', 'dip3', 'azimuth1', 'azimuth2', 'azimuth3'],
    isValid: function () {
      for (const itemId of this.itemIds) {
        let fieldCmp = this.getView().down(`#${itemId}`);
        if (fieldCmp.isHidden()) {
          continue;
        }
        if (fieldCmp.validate && !fieldCmp.validate()) {
          return false
        }
      }
      return true;
    },
    initComponent: function () {
      let channelInfo = this.getViewModel().get('channelInfo');
      for (const field of channelInfo.getFields()) {
        let fieldCmp = this.getView().down(`#${field.name}`);
        if (fieldCmp) {
          let record = new Ext.data.Model({
            name: fieldCmp.validationAttr,
            value: channelInfo.get(field.name),
            only_critical: true,
            node_type_id: yasmine.NodeTypeEnum.channel
          });

          fieldCmp.getViewModel().set('record', record)
        }
      }
    },
    storeStepData: function () {
      let channelInfo = this.getViewModel().get('channelInfo');
      let skipOrientation = !!this.getViewModel().get('hideDipAzimuth');
      for (const itemId of this.itemIds) {
        if (skipOrientation && (itemId.startsWith('dip') || itemId.startsWith('azimuth'))) {
          continue;
        }
        if (channelInfo.get(itemId) !== undefined) {
          let fieldCmp = this.getView().down(`#${itemId}`);
          channelInfo.set(itemId, fieldCmp.getViewModel().get('record').get('value'));
        }
      }
    },
    onValueChange: function () {
      let srNumber = this.getViewModel().get('sampleRateNumber');
      Ext.ux.Mediator.fireEvent(`wizardCreateChannelController-dataIsChanged-${srNumber}`);
    }
  },
  layout: {
    type: 'vbox',
    align: 'stretch',
    pack: 'start'
  },
  maxWidth: 420,
  minWidth: 0,
  items: [
    {
      xtype: 'fieldcontainer',
      fieldLabel: 'Channel',
      defaults: {
        flex: 1,
        minWidth: 0
      },
      layout: 'hbox',
      items: [
        {
          xtype: 'yasmine-text-field',
          itemId: 'code1',
          validationAttr: 'code',
          bind: {
            value: '{record.value}'
          },
          listeners: { change: 'onValueChange' }
        },
        {
          xtype: 'yasmine-text-field',
          itemId: 'code2',
          validationAttr: 'code',
          bind: {
            hidden: '{orientIsZ}',
            value: '{record.value}'
          },
          listeners: { change: 'onValueChange' }
        },
        {
          xtype: 'yasmine-text-field',
          itemId: 'code3',
          validationAttr: 'code',
          bind: {
            hidden: '{orientIsZ}',
            value: '{record.value}'
          },
          listeners: { change: 'onValueChange' }
        }
      ]
    },
    {
      xtype: 'fieldcontainer',
      fieldLabel: 'Dip',
      bind: {
        hidden: '{hideDipAzimuth}'
      },
      defaults: {
        flex: 1,
        minWidth: 0
      },
      layout: 'hbox',
      items: [
        {
          xtype: 'yasmine-float-field',
          itemId: 'dip1',
          validationAttr: 'dip',
          bind: {
            value: '{record.value}'
          },
          listeners: { change: 'onValueChange' }
        },
        {
          xtype: 'yasmine-float-field',
          itemId: 'dip2',
          validationAttr: 'dip',
          bind: {
            hidden: '{orientIsZ}',
            value: '{record.value}'
          },
          listeners: { change: 'onValueChange' }
        },
        {
          xtype: 'yasmine-float-field',
          itemId: 'dip3',
          validationAttr: 'dip',
          bind: {
            hidden: '{orientIsZ}',
            value: '{record.value}'
          },
          listeners: { change: 'onValueChange' }
        }
      ]
    },
    {
      xtype: 'fieldcontainer',
      fieldLabel: 'Azimuth',
      bind: {
        hidden: '{hideDipAzimuth}'
      },
      defaults: {
        flex: 1,
        minWidth: 0
      },
      layout: 'hbox',
      items: [
        {
          xtype: 'yasmine-float-field',
          itemId: 'azimuth1',
          validationAttr: 'azimuth',
          bind: {
            value: '{record.value}'
          },
          listeners: {change: 'onValueChange'}
        },
        {
          xtype: 'yasmine-float-field',
          itemId: 'azimuth2',
          validationAttr: 'azimuth',
          bind: {
            hidden: '{orientIsZ}',
            value: '{record.value}'
          },
          listeners: {change: 'onValueChange'}
        },
        {
          xtype: 'yasmine-float-field',
          itemId: 'azimuth3',
          validationAttr: 'azimuth',
          bind: {
            hidden: '{orientIsZ}',
            value: '{record.value}'
          },
          listeners: { change: 'onValueChange' }
        }
      ]
    }
  ]
});

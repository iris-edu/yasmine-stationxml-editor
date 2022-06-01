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


Ext.define('yasmine.view.xml.builder.wizard.networksteps.WizardCreateNetworkView', {
  extend: 'Ext.panel.Panel',
  xtype: 'wizard-create-network',
  controller: {
    initComponent: function () {
      let items = this.lookup('container').items;
      for (let i = 0; i < items.getCount(); i++) {
        let item = items.getAt(i);
        item.getViewModel().set('record', new Ext.data.Model({
          name: item.getItemId(),
          value: null,
          only_critical: true,
          node_type_id: yasmine.NodeTypeEnum.network
        }));
      }
    },
    isValid: function () {
      let items = this.lookup('container').items;
      return yasmine.utils.ValidatorUtil.triggerValidation(items);
    },
    fillStoredData: function () {
      let items = this.lookup('container').items;
      let data = this.getViewModel().get('networkStoredData');
      data.attributes = [];
      for (let i = 0; i < items.getCount(); i++) {
        let item = items.getAt(i);
        let record = item.getViewModel().get('record');
        if (record.get('value')) {
          data.attributes.push(record);
        }
        if (record.get('name') === 'code') {
          this.getViewModel().set('networkCode', record.get('value'));
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
      width: 300,
      reference: 'container',
      items: [
        {
          xtype: 'yasmine-text-field',
          itemId: 'code',
          fieldLabel: 'Network Code',
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
      ]
    }
  ]
});

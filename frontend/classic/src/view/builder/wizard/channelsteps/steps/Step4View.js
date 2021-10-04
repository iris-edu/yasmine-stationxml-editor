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


Ext.define('yasmine.view.xml.builder.wizard.channelsteps.steps.Step4View', {
  extend: 'Ext.panel.Panel',
  xtype: 'channel-step-4',
  controller: {
    isValid: function () {
      let items = this.getView().items;
      for (let i = 0; i < items.getCount(); i++) {
        let item = items.getAt(i);
        if (item.validate && !item.validate()) {
          return false;
        }
      }
      return true;
    },
    initComponent: function () {
      let viewModel = this.getViewModel();
      viewModel.set('codePrefix', null);
      viewModel.set('orient', null);

      let stepsData = this.getViewModel().get('stepsStoredData');
      if (stepsData.selectedLibrary === 'none') {
        return;
      }

      let dataloggerKeys = stepsData.dataloggerKeys;
      let sensorKeys = stepsData.sensorKeys;
      if (sensorKeys.length === 0 || dataloggerKeys.length === 0) {
        return;
      }

      let channelInfo = this.getViewModel().get('channelInfo');
      let me = this;
      let libraryType = stepsData.selectedLibrary;
      Ext.Ajax.request({
        scope: this,
        jsonData: {sensorKeys, dataloggerKeys, libraryType},
        url: '/api/wizard/guess/code/',
        method: 'POST',
        success: function (response) {
          let code = response.responseText;
          let codePrefix = '';
          if (code.length > 1) {
            codePrefix = code.substring(0, 2);
          }

          if (!code.endsWith('Z') && codePrefix) {
            channelInfo.set('code1', 'BDF');
          }

          me.getViewModel().set('codePrefix', codePrefix);
        }
      });
    },
    storeStepData: function () {
      let viewModel = this.getViewModel();
      let orient = viewModel.get('orient');
      let codePrefix = viewModel.get('codePrefix');
      let channelInfo = this.getViewModel().get('channelInfo');

      if (orient === yasmine.ChannelOrient.ZNE) {
        channelInfo.set('code1', codePrefix + 'Z')
        channelInfo.set('code2', codePrefix + 'N')
        channelInfo.set('code3', codePrefix + 'E')
        channelInfo.set('dip1', -90)
        channelInfo.set('dip2', 0)
        channelInfo.set('dip3', 0)
        channelInfo.set('azimuth1', 0)
        channelInfo.set('azimuth2', 0)
        channelInfo.set('azimuth3', 90)
      } else if (orient === yasmine.ChannelOrient.Z12) {
        channelInfo.set('code1', codePrefix + 'Z')
        channelInfo.set('code2', codePrefix + '1')
        channelInfo.set('code3', codePrefix + '2')
        channelInfo.set('dip1', 0)
        channelInfo.set('dip2', 0)
        channelInfo.set('dip3', 0)
        channelInfo.set('azimuth1', 0)
        channelInfo.set('azimuth2', 0)
        channelInfo.set('azimuth3', 0)
      } else if (orient === yasmine.ChannelOrient.Z) {
        channelInfo.set('code1', codePrefix + 'Z')
        channelInfo.set('code2', '')
        channelInfo.set('code3', '')
        channelInfo.set('dip1', 0)
        channelInfo.set('dip2', 0)
        channelInfo.set('dip3', 0)
        channelInfo.set('azimuth1', 0)
        channelInfo.set('azimuth2', 0)
        channelInfo.set('azimuth3', 0)
      }
    }
  },
  layout: {
    type: 'vbox',
    align: 'stretch',
    pack: 'start'
  },
  width: 400,
  defaults: {
    labelWidth: 150,
  },
  items: [
    {
      xtype: 'textfield',
      fieldLabel: 'Channel Prefix',
      reference: 'codePrefix',
      bind: '{codePrefix}',
      maxLength: 2,
      enforceMaxLength: true,
      allowBlank: false
    },
    {
      xtype: 'combobox',
      fieldLabel: 'Channel Orientation',
      bind: '{orient}',
      allowBlank: false,
      editable: false,
      displayField: 'name',
      valueField: 'id',
      store: {
        store: 'store.array',
        fields: ['id', 'name'],
        data: [
          [yasmine.ChannelOrient.ZNE, 'ZNE (3 channels)'],
          [yasmine.ChannelOrient.Z12, 'Z12 (3 channels)'],
          [yasmine.ChannelOrient.Z, 'Z (1 channel)']
        ]
      },
      forceSelection: true
    }
  ]
});

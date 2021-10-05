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


Ext.define('yasmine.view.xml.builder.wizard.finalsteps.WizardFinalStepView', {
  extend: 'Ext.panel.Panel',
  xtype: 'wizard-final-step',
  controller: {
    isValid: function () {
      let network = this.lookup('networkcheckbox').getValue();
      let station = this.lookup('stationcheckbox').getValue();
      let channel = this.lookup('channelcheckbox').getValue();
      let library = this.lookup('librarycombo').getValue();

      if ((network || station || channel) && !library) {
        Ext.Msg.alert('Error', 'Please select a user library', Ext.emptyFn);
        return false;
      }

      return true;
    },
    initComponent: function () {
      let networkCode = `<span style="color: red">${this.getViewModel().get('networkCode')}</span>`;
      let stationCode = `<span style="color: red">${this.getViewModel().get('stationCode')}</span>`;
      let channelNumber = `<span style="color: red">${this.findChannelNumber()}</span>`;

      this.initSummaryMessage(networkCode, stationCode, channelNumber);
      this.initNetwork(networkCode);
      this.initStation(stationCode);
      this.initChannel(channelNumber);
    },
    fillStoredData: function () {
      let data = this.getViewModel().get('finalStepStoreData');
      data.network = this.lookup('networkcheckbox').getValue();
      data.station = this.lookup('stationcheckbox').getValue();
      data.channel = this.lookup('channelcheckbox').getValue();
      data.userLibraryId = this.lookup('librarycombo').getValue();
    },
    findStationCode: function (modelField, attributeName) {
      let attributes = this.getViewModel().get(modelField).attributes;
      for (let attribute of attributes) {
        if (attribute.get('name') === attributeName) {
          return attribute.get('value');
        }
      }
      return '';
    },
    findChannelNumber: function () {
      let channelInfos = this.getViewModel().get('channelStoredData').channelInfos;
      let channelCounter = 0;
      for (let channelInfo of channelInfos) {
        if (channelInfo.get('code1')) {
          channelCounter++;
        }
        if (channelInfo.get('code2')) {
          channelCounter++;
        }
        if (channelInfo.get('code3')) {
          channelCounter++;
        }
      }
      return channelCounter;
    },
    initSummaryMessage: function (networkCode, stationCode, channelNumber) {
      let message = `<b>You have created ${channelNumber} channels for ${stationCode} station of ${networkCode} network.</b>`;
      this.lookup('message-panel').setHtml(message);
    },
    initNetwork: function (code) {
      let checkbox = this.lookup('networkcheckbox');
      let icon = this.getIconClass(yasmine.NodeTypeEnum.network);
      let label = `${icon} Add the ${code} network, its station and its channels to the network user library`;
      checkbox.setBoxLabel(label);
    },
    initStation: function (code) {
      let checkbox = this.lookup('stationcheckbox');
      let icon = this.getIconClass(yasmine.NodeTypeEnum.station);
      let label = `${icon} Add the ${code} station and its channels to the station user library`;
      checkbox.setBoxLabel(label);
    },
    initChannel: function (number) {
      let checkbox = this.lookup('channelcheckbox');
      let icon = this.getIconClass(yasmine.NodeTypeEnum.channel);
      let label = `${icon} Add ${number} created channels to the channel user library`;
      checkbox.setBoxLabel(label);
    },
    getIconClass: function (nodeEnum) {
      return `<i class="${yasmine.utils.NodeTypeConverter.toIcon(nodeEnum)}" style="font-style: normal;"></i>`;
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
      items: [
        {
          height: 50,
          reference: 'message-panel',
          html: 'N/A'
        },
        {
          xtype: 'checkboxfield',
          reference: 'networkcheckbox',
          boxLabel: 'N/A',
          name: 'topping',
          inputValue: '1',
        },
        {
          xtype: 'checkboxfield',
          reference: 'stationcheckbox',
          boxLabel: 'N/A',
          name: 'topping',
          inputValue: '1',
        },
        {
          xtype: 'checkboxfield',
          reference: 'channelcheckbox',
          boxLabel: 'N/A',
          name: 'topping',
          inputValue: '1',
        },
        {
          xtype: 'combobox',
          reference: 'librarycombo',
          fieldLabel: 'User Library',
          displayField: 'name',
          valueField: 'id',
          store: {
            model: 'yasmine.model.UserLibrary',
            autoLoad: true,
          },
          forceSelection: true,
          queryMode: 'local'
        }
      ]
    }
  ]
});

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


Ext.define('yasmine.view.xml.builder.wizard.channelsteps.WizardCreateChannelView', {
  extend: 'Ext.panel.Panel',
  xtype: 'wizard-create-channel',
  requires: [
    'yasmine.view.xml.builder.wizard.channelsteps.steps.WizardPerSampleRate',
    'yasmine.model.ChannelCreation'
  ],
  controller: {
    isValid: function () {
      return this.lookup('wizard-container')
        .getActiveTab()
        .getController()
        .isActiveItemValid();
    },
    isCompleted: function () {
      if (!this.isValid()) {
        return false;
      }
      let items = this.lookup('wizard-container').items;
      for (let i = 0; i < items.getCount(); i++) {
        if (!items.getAt(i).getController().isCompleted()) {
          return false;
        }
      }
      return true;
    },
    initComponent: function (startNodeId, startNodeType) {
      let container = this.lookup('wizard-container');
      container.removeAll(true, true);

      let stationNodeId = (startNodeType === yasmine.NodeTypeEnum.station) ? startNodeId : 0;
      yasmine.model.ChannelCreation.load(stationNodeId, {
        scope: this,
        success: function (channelInfo) {
          this.createChannelWizards(channelInfo);
        }
      });
    },
    createChannelWizards: function (channelInfo) {
      let container = this.lookup('wizard-container');
      container.setHidden(false);
      container.getTabBar().hide();
      container.removeAll(true, true);
      const count = this.getViewModel().get('stationStoredData').activeSampleRate;
      let firstTab;
      for (let i = 0; i < count; i++) {
        let content = Ext.create({
          xtype: 'wizard-per-sample-rate-channel',
          reference: `wizard-per-sample-rate-channel-${i}`
        });
        content.getViewModel().set('sampleRateNumber', i + 1);
        content.getViewModel().set('channelInfo', channelInfo.copy(null));
        content.getViewModel().set('stationAttributes', this.getViewModel().get('stationStoredData').attributes);
        content.getController().initComponent();

        container.add([content]);
        if (i === 0) {
          firstTab = content;
        }
      }

      container.suspendEvents();
      container.setActiveTab(firstTab);
      container.resumeEvents();
    },
    fillStoredData: function () {
      let data = this.getViewModel().get('channelStoredData');
      data.channelInfos = [];
      const count = this.getViewModel().get('stationStoredData').activeSampleRate;
      for (let i = 0; i < count; i++) {
        let wizard = this.lookup(`wizard-per-sample-rate-channel-${i}`);
        let channelInfo = wizard.getViewModel().get('channelInfo');
        data.channelInfos.push(channelInfo);
      }
    },
    hasWizard: function () {
      return true;
    },
    goNextIfValid: function () {
      if (!this.isValid()) {
        return;
      }
      let wizardContainer = this.lookup('wizard-container');
      let currentWizard = wizardContainer.getActiveTab();
      if (currentWizard.getController().isCompleted()) {
        let wizards = wizardContainer.items;
        for (let i = 0; i < wizards.getCount(); i++) {
          if (currentWizard.id === wizards.getAt(i).id) {
            currentWizard = wizards.getAt(i+1);
            wizardContainer.setActiveTab(currentWizard);
            break;
          }
        }
      } else {
        currentWizard.getController().showNext();
      }
    },
    isStart: function () {
      let wizardContainer = this.lookup('wizard-container');
      let currentWizard = wizardContainer.getActiveTab();
      return wizardContainer.items.indexOf(currentWizard) === 0 && currentWizard.getController().isStart();
    },
    geBackNestedWizard: function () {
      let wizardContainer = this.lookup('wizard-container');
      let currentWizard = wizardContainer.getActiveTab();
      if (currentWizard.getController().isStart()) {
        let previousIndex = wizardContainer.items.indexOf(currentWizard) - 1;
        wizardContainer.setActiveTab(wizardContainer.items.getAt(previousIndex));
      } else {
        currentWizard.getController().showPrevious();
      }
    }
  },
  layout: {
    type: 'vbox',
    align: 'stretch'
  },
  items: [
    {
      xtype: 'tabpanel',
      flex: 1,
      reference: 'wizard-container'
    }
  ]
});

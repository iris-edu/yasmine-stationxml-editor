/* ****************************************************************************
* 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
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
      if (!this.wantsLibrary()) {
        return true;
      }

      if (this.getLibraryMode() === 'new') {
        if (!this.getNewLibraryName()) {
          Ext.Msg.alert('Error', 'Please enter a name for the new user library', Ext.emptyFn);
          return false;
        }
        return true;
      }

      if (!this.lookup('librarycombo').getValue()) {
        let message = this.getLibraryStore().getCount()
          ? 'Please select a user library'
          : 'There are no user libraries yet. Create a new one.';
        Ext.Msg.alert('Error', message, Ext.emptyFn);
        return false;
      }

      return true;
    },
    initComponent: function () {
      let viewModel = this.getViewModel();
      let networkCode = `<span style="color: red">${(viewModel && viewModel.get('networkCode')) || ''}</span>`;
      let stationCode = `<span style="color: red">${(viewModel && viewModel.get('stationCode')) || ''}</span>`;
      let channelNumber = `<span style="color: red">${this.findChannelNumber()}</span>`;

      this.initSummaryMessage(networkCode, stationCode, channelNumber);
      this.initNetwork(networkCode);
      this.initStation(stationCode);
      this.initChannel(channelNumber);
      this.refreshLibraryChoice();
    },
    fillStoredData: function () {
      let data = this.getViewModel().get('finalStepStoreData');
      data.network = this.lookup('networkcheckbox').getValue();
      data.station = this.lookup('stationcheckbox').getValue();
      data.channel = this.lookup('channelcheckbox').getValue();

      if (!this.wantsLibrary()) {
        data.userLibraryId = null;
        return true;
      }

      if (this.getLibraryMode() === 'new') {
        let libraryId = this.createLibrary(this.getNewLibraryName());
        if (!libraryId) {
          return false;
        }
        data.userLibraryId = libraryId;
        return true;
      }

      data.userLibraryId = this.lookup('librarycombo').getValue();
      return true;
    },
    wantsLibrary: function () {
      return !!(
        this.lookup('networkcheckbox').getValue() ||
        this.lookup('stationcheckbox').getValue() ||
        this.lookup('channelcheckbox').getValue()
      );
    },
    getLibraryStore: function () {
      return this.lookup('librarycombo').getStore();
    },
    getLibraryMode: function () {
      return this.lookup('librarymodenew').getValue() ? 'new' : 'existing';
    },
    getNewLibraryName: function () {
      return (this.lookup('newlibraryname').getValue() || '').trim();
    },
    setLibraryMode: function (mode) {
      this._applyingLibraryMode = true;
      this.lookup('librarymodenew').setValue(mode === 'new');
      this.lookup('librarymodeexisting').setValue(mode === 'existing');
      this._applyingLibraryMode = false;
      this.syncLibraryFields();
    },
    onLibraryModeChange: function (radio, checked) {
      if (!checked || this._applyingLibraryMode) {
        return;
      }
      this.libraryModeTouched = true;
      this.syncLibraryFields();
    },
    syncLibraryFields: function () {
      let creating = this.getLibraryMode() === 'new';
      this.lookup('librarycombo').setHidden(creating);
      this.lookup('newlibraryname').setHidden(!creating);
    },
    refreshLibraryChoice: function () {
      let store = this.getLibraryStore();
      if (store.isLoaded()) {
        this.applyLibraryAvailability(store.getCount());
        return;
      }
      if (this._libraryLoadBound) {
        return;
      }
      this._libraryLoadBound = true;
      store.on('load', function (loadedStore, records, successful) {
        if (!this.getView() || this.getView().destroyed) {
          return;
        }
        this.applyLibraryAvailability(successful ? loadedStore.getCount() : 0);
      }, this);
    },
    applyLibraryAvailability: function (count) {
      let existing = this.lookup('librarymodeexisting');
      let hint = this.lookup('libraryhint');
      let hasLibraries = count > 0;
      existing.setDisabled(!hasLibraries);
      existing.setBoxLabel(hasLibraries
        ? 'Use an existing library'
        : 'Use an existing library (none yet)');
      if (!hasLibraries) {
        hint.setHtml('There are no user libraries yet. Create a new one to save this network, station, and channels.');
        this.setLibraryMode('new');
        return;
      }
      hint.setHtml('Choose an existing library or create a new one.');
      if (!this.libraryModeTouched) {
        this.setLibraryMode('existing');
        this.selectOnlyLibrary();
      } else {
        this.syncLibraryFields();
      }
    },
    selectOnlyLibrary: function () {
      let combo = this.lookup('librarycombo');
      let store = combo.getStore();
      if (!combo.getValue() && store.getCount() === 1) {
        combo.setValue(store.first().get('id'));
      }
    },
    createLibrary: function (name) {
      let request;
      try {
        request = Ext.Ajax.request({
          url: '/api/user-library/',
          method: 'POST',
          async: false,
          jsonData: { name: name }
        });
      } catch (e) {
        Ext.Msg.alert('Error', 'Unable to create the user library', Ext.emptyFn);
        return null;
      }
      let result = null;
      try {
        result = JSON.parse((request && request.responseText) || '{}');
      } catch (e) {
        result = null;
      }
      if (!result || !result.success || !result.data || result.data.id == null) {
        Ext.Msg.alert('Error', (result && result.message) || 'Unable to create the user library', Ext.emptyFn);
        return null;
      }
      return result.data.id;
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
      let stored = this.getViewModel() && this.getViewModel().get('channelStoredData');
      let channelInfos = (stored && stored.channelInfos) || [];
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
      let panel = this.lookup('message-panel');
      if (panel) {
        panel.setHtml(message);
      }
    },
    initNetwork: function (code) {
      let checkbox = this.lookup('networkcheckbox');
      if (!checkbox) {
        return;
      }
      let icon = this.getIconClass(yasmine.NodeTypeEnum.network);
      checkbox.setBoxLabel(`${icon} Add the ${code} network, its station and its channels to the network user library`);
    },
    initStation: function (code) {
      let checkbox = this.lookup('stationcheckbox');
      if (!checkbox) {
        return;
      }
      let icon = this.getIconClass(yasmine.NodeTypeEnum.station);
      checkbox.setBoxLabel(`${icon} Add the ${code} station and its channels to the station user library`);
    },
    initChannel: function (number) {
      let checkbox = this.lookup('channelcheckbox');
      if (!checkbox) {
        return;
      }
      let icon = this.getIconClass(yasmine.NodeTypeEnum.channel);
      checkbox.setBoxLabel(`${icon} Add ${number} created channels to the channel user library`);
    },
    getIconClass: function (nodeEnum) {
      return `<i class="${yasmine.utils.NodeTypeConverter.toIcon(nodeEnum)}" style="font-style: normal;"></i>`;
    }
  },
  layout: {
    type: 'vbox',
    align: 'stretch'
  },
  scrollable: 'y',
  items: [
    {
      xtype: 'container',
      flex: 1,
      maxWidth: 720,
      minWidth: 0,
      padding: '16 24',
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
          xtype: 'fieldset',
          title: 'User Library',
          margin: '16 0 0 0',
          layout: {
            type: 'vbox',
            align: 'stretch'
          },
          items: [
            {
              xtype: 'component',
              reference: 'libraryhint',
              margin: '0 0 8 0',
              html: 'Choose an existing library or create a new one.'
            },
            {
              xtype: 'radiofield',
              reference: 'librarymodeexisting',
              name: 'wizardLibraryMode',
              boxLabel: 'Use an existing library',
              inputValue: 'existing',
              disabled: true,
              listeners: {
                change: 'onLibraryModeChange'
              }
            },
            {
              xtype: 'combobox',
              reference: 'librarycombo',
              margin: '4 0 12 24',
              hideLabel: true,
              hidden: true,
              emptyText: 'Select a library',
              displayField: 'name',
              valueField: 'id',
              store: {
                model: 'yasmine.model.UserLibrary',
                autoLoad: true,
                sorters: [{
                  property: 'name',
                  direction: 'ASC'
                }]
              },
              forceSelection: true,
              queryMode: 'local',
              listConfig: {
                emptyText: 'No libraries yet'
              }
            },
            {
              xtype: 'radiofield',
              reference: 'librarymodenew',
              name: 'wizardLibraryMode',
              boxLabel: 'Create a new library',
              inputValue: 'new',
              checked: true,
              listeners: {
                change: 'onLibraryModeChange'
              }
            },
            {
              xtype: 'textfield',
              reference: 'newlibraryname',
              margin: '4 0 0 24',
              hideLabel: true,
              emptyText: 'New library name',
              maxLength: 50,
              enforceMaxLength: true
            }
          ]
        }
      ]
    }
  ]
});

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


Ext.define('yasmine.view.xml.builder.wizard.WizardCreateController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.wizard-create',
  requires: [
    'Ext.ux.Mediator',
  ],
  init: function () {
    this.getView().addListener('show', this.onShow, this);
  },
  onShow: function () {
    this.activateItem(0);
    this.initActiveItem();
  },
  onNext: function () {
    if (this.hasActiveItemNestedWizard() && !this.isActiveItemNestedWizardCompleted()) {
      this.getActiveItemController().goNextIfValid();
    } else if (this.isActiveItemValid()) {
      this.fillStoredDataFromActiveItem();
      this.activateItem(1);
      this.initActiveItem();
    }
  },
  onPrevious: function () {
    if (this.hasActiveItemNestedWizard() && !this.isActiveItemNestedWizardStart()) {
      this.getActiveItemController().geBackNestedWizard();
    } else if (!this.getViewModel().get('hasNext')) {
      this.onConfirmToGoToPreviousClick('yes');
    } else {
      Ext.Msg.confirm(
        'Warning',
        'Are you sure you want to go to the previous step? The data for the current step will be deleted',
        (buttonId) => this.onConfirmToGoToPreviousClick(buttonId));
    }
  },
  onConfirmToGoToPreviousClick: function (buttonId) {
    if (buttonId === 'yes') {
      this.activateItem(-1);
    }
  },
  activateItem: function (delta) {
    let nextIndex = this.getViewModel().get('currentIndex') + delta;
    let layout = this.getView().getLayout();
    layout.setActiveItem(nextIndex);
    this.getViewModel().set('currentIndex', nextIndex);
  },
  isActiveItemValid: function () {
    let controller = this.getActiveItemController();
    if (controller && controller.isValid) {
      return controller.isValid();
    }
    return true;
  },
  fillStoredDataFromActiveItem: function () {
    let controller = this.getActiveItemController();
    if (controller && controller.fillStoredData) {
      controller.fillStoredData();
    }
  },
  initActiveItem: function () {
    let controller = this.getActiveItemController();
    if (controller && controller.initComponent) {
      let viewModel = this.getViewModel();
      controller.initComponent(viewModel.get('startNodeId'), viewModel.get('startNodeType'));
    }
  },
  getActiveItemController: function () {
    return this.getView().getLayout().activeItem.getController();
  },
  hasActiveItemNestedWizard: function () {
    let controller = this.getActiveItemController();
    return controller && controller.hasWizard && controller.hasWizard();
  },
  isActiveItemNestedWizardCompleted: function () {
    let controller = this.getActiveItemController();
    return controller && controller.hasWizard && controller.isCompleted();
  },
  isActiveItemNestedWizardStart: function () {
    let controller = this.getActiveItemController();
    return controller && controller.hasWizard && controller.isStart();
  },
  onMaximizeClick: function () {
    this.getView().maximized
      ? this.getView().restore()
      : this.getView().maximize();
  },
  onCancelClick: function () {
    this.getView().close();
  },
  onSave: function () {
    if (!this.isActiveItemValid()) {
      return;
    }

    this.fillStoredDataFromActiveItem();

    let networkId = this.createNetwork();
    this.getViewModel().set('networkId', networkId);
    let stationId = this.createStation(networkId);
    this.getViewModel().set('stationId', stationId);
    let channelIds = this.createChannels(stationId);
    this.getViewModel().set('channelIds', channelIds);

    this.addToLibrary();

    this.getView().fireEvent('saved', null);
    this.getView().close();
  },
  createNetwork: function () {
    let networkId = this.getViewModel().get('networkId');
    if (networkId) {
      return networkId;
    }
    let attributes = this.getViewModel().get('networkStoredData').attributes;
    let network = Ext.create('yasmine.model.NetworkCreation');
    network.setId(-1);
    network.set('xmlId', this.getViewModel().get('xmlId'));
    for (const attribute of attributes) {
      network.set(attribute.get('name'), attribute.get('value'));
    }

    let request = Ext.Ajax.request({
      scope: this,
      async: false,
      jsonData: network.getData(),
      url: network.getProxy().getUrl(),
      method: 'POST'
    });

    return JSON.parse(request.responseText).network_id;
  },
  createStation: function (networkId) {
    let stationId = this.getViewModel().get('stationId');
    if (stationId) {
      return stationId;
    }
    let attributes = this.getViewModel().get('stationStoredData').attributes;
    let station = Ext.create('yasmine.model.StationCreation');
    station.setId(-1);
    station.set('xmlId', this.getViewModel().get('xmlId'));
    station.set('networkNodeId', networkId);
    for (const attribute of attributes) {
      station.set(attribute.get('name'), attribute.get('value'));
    }

    let request = Ext.Ajax.request({
      scope: this,
      async: false,
      jsonData: station.getData(),
      url: station.getProxy().getUrl(),
      method: 'POST'
    });

    return JSON.parse(request.responseText).station_id;
  },
  createChannels: function (stationId) {
    let channelInfos = this.getViewModel().get('channelStoredData').channelInfos;
    let channelIds = [];
    for (let channelInfo of channelInfos) {
      channelInfo.setId(-1);
      channelInfo.set('xmlId', this.getViewModel().get('xmlId'));
      channelInfo.set('stationNodeId', stationId);
      let request = Ext.Ajax.request({
        scope: this,
        async: false,
        jsonData: channelInfo.getData(),
        url: '/api/wizard/new-channel/',
        method: 'POST'
      });

      let result = JSON.parse(request.responseText).channel_ids;
      for (const channelId of result) {
        channelIds.push(channelId);
      }
    }

    return channelIds;
  },
  addToLibrary: function () {
    let lib = this.getViewModel().get('finalStepStoreData');
    let userLibraryId = lib.userLibraryId;

    if (lib.network) {
      let networkId = this.getViewModel().get('networkId');
      this.addToLibraryAjax(userLibraryId, yasmine.NodeTypeEnum.network, networkId);
    }
    if (lib.station) {
      let stationId = this.getViewModel().get('stationId');
      this.addToLibraryAjax(userLibraryId, yasmine.NodeTypeEnum.station, stationId);
    }
    if (lib.channel) {
      let channelIds = this.getViewModel().get('channelIds');
      for (const channelId of channelIds) {
        this.addToLibraryAjax(userLibraryId, yasmine.NodeTypeEnum.channel, channelId);
      }
    }
  },
  addToLibraryAjax: function (libraryId, nodeType, nodeId) {
    Ext.Ajax.request({
      url: '/api/user-library/node/',
      async: false,
      jsonData: {
        libraryId: libraryId,
        nodeType: nodeType,
        parentNodeId: null,
        nodeIdToClone: nodeId
      },
      method: 'POST',
    });
  }
});

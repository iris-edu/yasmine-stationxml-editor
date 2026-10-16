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


Ext.define('yasmine.view.xml.builder.wizard.WizardCreateController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.wizard-create',
  requires: [
    'Ext.ux.Mediator',
    'yasmine.utils.HelpUtil',
    'yasmine.utils.StationXmlHelpContext'
  ],
  init: function () {
    this.lastHelpField = null;
    this.getView().addListener('show', this.onShow, this);
    this.getView().on('afterrender', this.bindHelpFocus, this);
    this.mon(Ext.ux.Mediator, 'wizard-updateActionButtons', this.updateWizardActionButtons, this);
  },
  bindHelpFocus: function () {
    var view = this.getView();
    if (view && view.el && view.el.dom) {
      view.el.dom.addEventListener('focusin', this.onWizardFocusIn.bind(this));
    }
  },
  onWizardFocusIn: function (event) {
    var field = this.fieldFromEvent(event);
    if (field) {
      this.lastHelpField = field;
    }
  },
  fieldFromEvent: function (event) {
    var target = event && (event.target || event.getTarget && event.getTarget());
    var component = target && Ext.Component.fromElement(target, this.getView().el);
    var fallback = null;
    while (component && component !== this.getView()) {
      if (component.isXType && component.isXType('radio')) {
        return component.up('radiogroup') || component;
      }
      if (component.isXType && component.isXType('fieldcontainer') && target) {
        var nested = this.fieldContaining(component, target);
        if (nested) {
          return nested;
        }
      }
      if (component.isFormField && !component.isXType('displayfield')) {
        if (this.helpIdentity(component)) {
          return component;
        }
        fallback = fallback || component;
      }
      component = component.up();
    }
    return fallback;
  },
  fieldContaining: function (container, target) {
    var fields = container.query ? container.query('[isFormField]') : [];
    var match = null;
    Ext.Array.each(fields, function (field) {
      if (field.el && field.el.contains(target) && !field.isXType('fieldcontainer')) {
        match = field;
      }
    });
    return match;
  },
  helpIdentity: function (field) {
    var Context = yasmine.utils.StationXmlHelpContext;
    var itemId = field.itemId || (field.getItemId && field.getItemId());
    var validationAttr = field.validationAttr ||
      (field.initialConfig && field.initialConfig.validationAttr);
    var viewModel = field.getViewModel && field.getViewModel();
    var record = viewModel && viewModel.get('record');
    return !!(
      validationAttr ||
      (itemId && Context.ITEM_PARAMETERS[itemId]) ||
      (record && record.get && record.get('name'))
    );
  },
  currentNodeType: function () {
    var index = this.getViewModel().get('currentIndex');
    if (index === 0) {
      return yasmine.NodeTypeEnum.network;
    }
    if (index === 1) {
      return yasmine.NodeTypeEnum.station;
    }
    if (index === 2) {
      return yasmine.NodeTypeEnum.channel;
    }
    return null;
  },
  helpFieldDescriptor: function (field) {
    var record = field && field.getViewModel && field.getViewModel() &&
      field.getViewModel().get('record');
    var parameterName = record && record.get ? record.get('name') : null;
    var recordNodeType = record && record.get ? record.get('node_type_id') : null;
    return {
      nodeType: this.currentNodeType(),
      recordNodeType: recordNodeType,
      parameterName: parameterName,
      itemId: field && field.getItemId ? field.getItemId() : null,
      reference: field && (
        field.reference ||
        (field.initialConfig && field.initialConfig.reference)
      ),
      validationAttr: field && (
        field.validationAttr ||
        (field.initialConfig && field.initialConfig.validationAttr)
      ),
      fieldLabel: this.fieldLabelForHelp(field),
      inDataloggerModifier: !!(field && field.up('[reference=dataloggerModifierForm]')),
      inSensorModifier: !!(field && field.up('[reference=sensorModifierForm]')),
      inResponseSelector: !!(field && (
        field.up('nrl-response-selector') ||
        field.up('nrlv2-response-selector') ||
        field.up('arol-response-selector')
      ))
    };
  },
  fieldLabelForHelp: function (field) {
    var label = field && field.getFieldLabel ? field.getFieldLabel() : '';
    if (String(label || '').replace(/<[^>]*>/g, '').trim()) {
      return label;
    }
    var container = field && field.up && field.up('fieldcontainer');
    if (container && container.getFieldLabel) {
      return container.getFieldLabel();
    }
    return label;
  },
  onHelpClick: function () {
    var field = this.lastHelpField;
    if (field && (field.destroyed || field.isDestroyed || !field.isVisible(true))) {
      field = null;
    }
    var request = yasmine.utils.StationXmlHelpContext.wizardHelpRequest(
      field ? this.helpFieldDescriptor(field) : {
        nodeType: this.currentNodeType()
      }
    );
    yasmine.utils.HelpUtil.stationXmlHelpMe(request.context, request.title);
  },
  updateWizardActionButtons: function (buttons) {
    let container = this.lookupReference('wizard-action-buttons-container');
    if (!container) {
      return;
    }
    Ext.suspendLayouts();
    container.removeAll(false);
    container.hidden = false;
    if (container.show) {
      container.show();
    }
    if (container.el) {
      container.el.setDisplayed(true);
    }
    (buttons || []).forEach(function (button) {
      container.add(button);
    });
    Ext.resumeLayouts(true);
  },
  onShow: function () {
    if (!this.getView() || this.getView().destroyed || !this.getViewModel()) {
      return;
    }
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
        'Go back to the previous step? Answers already entered stay available.',
        (buttonId) => this.onConfirmToGoToPreviousClick(buttonId));
    }
  },
  onConfirmToGoToPreviousClick: function (buttonId) {
    if (buttonId === 'yes') {
      this.activateItem(-1);
    }
  },
  activateItem: function (delta) {
    let view = this.getView();
    let viewModel = this.getViewModel();
    if (!view || view.destroyed || !viewModel) {
      return;
    }
    let nextIndex = viewModel.get('currentIndex') + delta;
    let layout = view.getLayout();
    layout.setActiveItem(nextIndex);
    viewModel.set('currentIndex', nextIndex);
    viewModel.notify();
    view.setTitle(viewModel.get('currentTitle'));
    Ext.ux.Mediator.fireEvent('wizard-updateActionButtons', []);
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
      return controller.fillStoredData();
    }
    return true;
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
    var win = this.getView();
    if (win.maximized) {
      win.restore();
      yasmine.utils.ResponsiveUtil.fitWindow(win, {
        minWidth: 800,
        minHeight: 500,
        width: 1000,
        height: 700
      });
    } else {
      win.maximize();
    }
  },
  onCancelClick: function () {
    this.getView().close();
  },
  onSave: function () {
    if (!this.isActiveItemValid()) {
      return;
    }

    if (this.fillStoredDataFromActiveItem() === false) {
      return;
    }

    let networkId = this.createNetwork();
    if (!networkId) {
      return;
    }
    this.getViewModel().set('networkId', networkId);
    let stationId = this.createStation(networkId);
    if (!stationId) {
      return;
    }
    this.getViewModel().set('stationId', stationId);
    let channelIds = this.createChannels(stationId);
    if (!channelIds) {
      return;
    }
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
    if (!this.requestOk(request)) {
      Ext.Msg.alert('Error', 'Unable to create the network');
      return null;
    }
    let payload = this.parseJson(request);
    if (payload.success === false || !payload.network_id) {
      Ext.Msg.alert('Error', payload.message || 'Unable to create the network');
      return null;
    }
    return payload.network_id;
  },
  requestOk: function (request) {
    return request && request.status >= 200 && request.status < 300;
  },
  parseJson: function (request) {
    try {
      return JSON.parse((request && request.responseText) || '{}');
    } catch (e) {
      return {};
    }
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
    if (!this.requestOk(request)) {
      Ext.Msg.alert('Error', 'Unable to create the station');
      return null;
    }
    let payload = this.parseJson(request);
    if (payload.success === false || !payload.station_id) {
      Ext.Msg.alert('Error', payload.message || 'Unable to create the station');
      return null;
    }
    return payload.station_id;
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

      if (!this.requestOk(request)) {
        Ext.Msg.alert('Error', 'Unable to create channels');
        return null;
      }
      let payload = this.parseJson(request);
      if (payload.success === false) {
        Ext.Msg.alert('Error', payload.message || 'Unable to create channels');
        return null;
      }
      let result = payload.channel_ids || [];
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

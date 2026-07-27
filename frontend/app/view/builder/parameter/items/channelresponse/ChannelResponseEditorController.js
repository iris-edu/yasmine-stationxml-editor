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
* NRLv2 online support (2026): ASGSR, Alexey Emanov.
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


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.ChannelResponseEditorController', {
  extend: 'yasmine.view.xml.builder.parameter.ParameterItemEditorController',
  alias: 'controller.channel-response-editor',
  requires: [
    'Ext.ux.Mediator',
    'yasmine.utils.ResponseRecalculateUtil',
    'yasmine.view.xml.builder.parameter.items.channelresponse.preview.ResponsePreview',
    'yasmine.view.xml.builder.parameter.items.channelresponse.selectors.SelectorsContainer',
    'yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.ChannelResponseTreeEditor',
    'yasmine.view.xml.builder.parameter.items.channelresponse.nrl.NrlResponseSelector',
    'yasmine.view.xml.builder.parameter.items.channelresponse.arol.ArolResponseSelector',
    'yasmine.view.xml.builder.parameter.items.channelresponse.nrlv2.Nrlv2ResponseSelector'
  ],
  init: function () {
    this.callParent(arguments);
    Ext.GlobalEvents.on('nrlv2SettingsChanged', function () {
      let vm = this.getViewModel();
      if (vm) vm.set('settingsUpdatedAt', Date.now());
    }, this);
  },
  initData: function () {
    let record = this.getViewModel().get('record');
    let value = record.get('value');
    if (value) {
      this.getViewModel().set('channelResponseText', value);
      this.loadChannelResponsePlot();
      this.createPreview();
      return;
    }

    this.createResponseSelector();
  },
  fillRecord: function () {
    let currentViewRef = this.getViewModel().get('currentViewReference');
    let record = this.getViewModel().get('record');
    if (currentViewRef === 'response-preview') {
      let value = record.get('value');
      if (value && value.response) {
        return;
      }
      return;
    }
    let currentView = this.lookup(currentViewRef);
    if (!currentView && yasmine.utils.ResponseRecalculateUtil.SELECTOR_XTYPES.indexOf(currentViewRef) >= 0) {
      currentView = this.getView().items.getAt(0);
    }
    if (currentView && currentView.getController && currentView.getController().fillRecord) {
      currentView.getController().fillRecord();
      return;
    }
    if (currentViewRef === 'selectors-container') {
      return;
    }
    let child = this.getView().items.getAt(0);
    if (child && child.getController && child.getController().fillRecord) {
      child.getController().fillRecord();
    }
  },
  validate: function () {
    return true;
  },
  createPreview: function () {
    this.createComponent('response-preview', this.createActionButtons(), false);
  },
  createResponseSelector: function () {
    this.createComponent('selectors-container', [], false);
  },
  createNrlResponseSelector: function () {
    this.createComponent('nrl-response-selector', [], false);
  },
  createArolResponseSelector: function () {
    this.createComponent('arol-response-selector', [], false);
  },
  createNrlv2ResponseSelector: function () {
    this.createComponent('nrlv2-response-selector', [], false);
  },
  createXmlResponseEditor: function () {
    this.createComponent('channel-response-tree-editor', this.createTreeEditorActionButtons(), true);
  },
  createComponent(name, actionButtons, canSave) {
    this.getViewModel().set('currentViewReference', name);
    let container = this.getView();
    container.removeAll(true, true);
    container.add(Ext.create({xtype: name}));

    Ext.ux.Mediator.fireEvent('parameterEditorController-updateActionButtons', actionButtons);
    Ext.ux.Mediator.fireEvent('parameterEditorController-canSaveButton', canSave);
    this.syncSelectorActionButtons(name);
  },
  syncSelectorActionButtons: function (viewName) {
    let name = viewName || this.getViewModel().get('currentViewReference');
    if (yasmine.utils.ResponseRecalculateUtil.SELECTOR_XTYPES.indexOf(name) < 0) {
      return;
    }
    let child = this.getView().items.getAt(0);
    if (!child || !child.getViewModel) {
      return;
    }
    let ctrl = child.getController();
    if (ctrl && typeof ctrl.syncActiveSelectorTab === 'function') {
      ctrl.syncActiveSelectorTab();
    }
    yasmine.utils.ResponseRecalculateUtil.updateParameterEditorActionButtons(child.getViewModel());
  },
  createActionButtons: function () {
    return [
      Ext.create({
        xtype: 'button',
        text: 'Edit Response',
        iconCls: 'x-fa fa-pencil',
        handler: () => this.createXmlResponseEditor()
      }),
      Ext.create({
        xtype: 'button',
        text: 'Select a new Response',
        iconCls: 'x-fa fa-pencil',
        handler: () => this.createResponseSelector()
      }),
      this.createRecalculateSensitivityButton()
    ]
  },
  createTreeEditorActionButtons: function () {
    return [this.createRecalculateSensitivityButton()];
  },
  createRecalculateSensitivityButton: function () {
    return Ext.create({
      xtype: 'button',
      text: 'Recalculate Sensitivity',
      iconCls: 'x-fa fa-calculator',
      handler: () => this.recalculateSensitivity()
    });
  },
  recalculateSensitivity: function () {
    let that = this;
    let vm = this.getViewModel();
    let record = vm.get('record');
    let nodeInstanceId = record.get('node_inst_id');
    let currentViewRef = vm.get('currentViewReference');
    let payload = {
      nodeInstanceId: nodeInstanceId,
      min: vm.get('minFrequency'),
      max: vm.get('maxFrequency')
    };

    let pendingValue = record.get('value');
    if (pendingValue && pendingValue.response) {
      payload.response = pendingValue.response;
    }

    if (currentViewRef === 'channel-response-tree-editor') {
      let treeView = this.lookup('channel-response-tree-editor') || this.getView().items.getAt(0);
      if (treeView && treeView.getController) {
        let treeCtrl = treeView.getController();
        let store = treeCtrl.lookup('channelresponsetree').getStore();
        payload.response = treeCtrl.prepareResponse(store.getRoot().data.children);
      }
    }

    Ext.Ajax.request({
      method: 'POST',
      url: '/api/channel/response/recalculate-sensitivity/',
      jsonData: payload,
      success: function (response) {
        let result = JSON.parse(response.responseText);
        if (!result.success) {
          Ext.MessageBox.show({
            title: 'An error occurred',
            msg: result.message,
            buttons: Ext.MessageBox.OK,
            icon: Ext.MessageBox['ERROR']
          });
          return;
        }

        vm.set('channelResponseText', result.text);
        vm.set('channelResponseImageUrl', result.plot_url);
        vm.set('channelResponseCsvUrl', result.csv_url);
        record.set('value', {
          nodeId: record.get('nodeId'),
          response: result.data
        });
        Ext.ux.Mediator.fireEvent('parameterEditorController-canSaveButton', true);

        if (currentViewRef === 'channel-response-tree-editor') {
          let treeView = that.lookup('channel-response-tree-editor') || that.getView().items.getAt(0);
          if (treeView && treeView.getController) {
            let selectedKey = 'InstrumentSensitivity';
            let tree = treeView.getController().lookupReference('channelresponsetree');
            let selection = tree.getSelection()[0];
            if (selection && selection.get('key')) {
              selectedKey = selection.get('key');
            }
            treeView.getController().reloadTree(result.data, selectedKey);
          }
        }
      },
      failure: function () {
        Ext.MessageBox.show({
          title: 'An error occurred',
          msg: 'Cannot recalculate sensitivity.',
          buttons: Ext.MessageBox.OK,
          icon: Ext.MessageBox['ERROR']
        });
      }
    });
  },
  downloadChannelResponsePlot: function () {
    let win = window.open('', '_blank');
    win.location = this.getViewModel().get('channelResponseImageUrl');
    win.focus();
  },
  downloadChannelResponseCsv: function () {
    let win = window.open('', '_self');
    win.location = this.getViewModel().get('channelResponseCsvUrl');
    win.focus();
  },
  loadChannelResponsePlot: function () {
    let record = this.getViewModel().get('record');
    let pendingValue = record && record.get('value');
    if (pendingValue && pendingValue.response) {
      this.recalculateSensitivity();
      return;
    }

    let that = this;
    let nodeInstanceId = record.get('node_inst_id');
    let min = this.getViewModel().get('minFrequency');
    let max = this.getViewModel().get('maxFrequency');
    Ext.Ajax.request({
      method: 'GET',
      params: {nodeInstanceId, min, max},
      url: `/api/channel/response/plot-url/`,
      success: function (response, options) {
        let result = JSON.parse(response.responseText);
        if (!result.success) {
          Ext.MessageBox.show({
            title: 'An error occurred',
            msg: result.message,
            buttons: Ext.MessageBox.OK,
            icon: Ext.MessageBox['ERROR']
          });
        } else {
          that.getViewModel().set('channelResponseImageUrl', result.plot_url);
          that.getViewModel().set('channelResponseCsvUrl', result.csv_url);
        }
      }
    });
  }
});

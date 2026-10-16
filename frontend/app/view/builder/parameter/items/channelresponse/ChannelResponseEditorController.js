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
* 2026-09-28, version 4.4.0-beta: ASGSR, Alexey Emanov
* 2026-09-29, version 4.4.0-beta: ASGSR, Alexey Emanov
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
    'yasmine.view.xml.builder.parameter.items.channelresponse.selectors.respupload.RespUploadSelector',
    'yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.ChannelResponseTreeEditor',
    'yasmine.view.xml.builder.parameter.items.channelresponse.nrl.NrlResponseSelector',
    'yasmine.view.xml.builder.parameter.items.channelresponse.nrl.NrlResponseTypeSelector',
    'yasmine.view.xml.builder.parameter.items.channelresponse.arol.ArolResponseSelector',
    'yasmine.view.xml.builder.parameter.items.channelresponse.nrlv2.Nrlv2ResponseSelector'
  ],
  init: function () {
    this.callParent(arguments);
    this.mon(Ext.GlobalEvents, 'nrlv2SettingsChanged', function () {
      let vm = this.getViewModel();
      if (vm) vm.set('settingsUpdatedAt', Date.now());
    }, this);
  },
  initData: function () {
    let record = this.getViewModel().get('record');
    let value = record.get('value');
    if (value) {
      this.getViewModel().set('channelResponseText', value);
      this.createPreview();
      this.getViewModel().set('plotLoading', true);
      this.loadChannelResponsePlot();
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
  prepareRecordForSave: function () {
    let record = this.getViewModel().get('record');
    if (!record) {
      return true;
    }
    if (typeof record.get('value') !== 'string') {
      return true;
    }
    record.reject();
    return false;
  },
  validate: function () {
    let currentViewRef = this.getViewModel().get('currentViewReference');
    let currentView = this.lookup(currentViewRef) || this.getView().items.getAt(0);
    if (currentView && currentView.getController) {
      let controller = currentView.getController();
      if (controller && controller.validate) {
        return controller.validate();
      }
    }
    return true;
  },
  createPreview: function (canSave) {
    this.createComponent('response-preview', [], !!canSave);
  },
  createResponseSelector: function () {
    yasmine.utils.ResponseRecalculateUtil.clearPlotStageRange(this.getViewModel());
    this.createComponent('selectors-container', [], false);
  },
  createNrlResponseSelector: function () {
    this._pendingNrlLibrary = 'nrl';
    this.createComponent('nrl-response-type-selector', [], false);
  },
  createArolResponseSelector: function () {
    this.createComponent('arol-response-selector', [], false);
  },
  createNrlv2ResponseSelector: function () {
    this._pendingNrlLibrary = 'nrlv2_online';
    this.createComponent('nrl-response-type-selector', [], false);
  },
  createRespUploadSelector: function () {
    this.createComponent('resp-upload-selector', [], false);
  },
  openNrlSelector: function (responseType) {
    let library = this._pendingNrlLibrary || 'nrl';
    let xtype = library === 'nrlv2_online' ? 'nrlv2-response-selector' : 'nrl-response-selector';
    let element = (responseType === 'integrated' || responseType === 'soh') ? responseType : null;
    this.createComponent(xtype, [], false, {responseElement: element});
  },
  createXmlResponseEditor: function () {
    this.createComponent('channel-response-tree-editor', this.createTreeEditorActionButtons(), true);
  },
  createComponent: function (name, actionButtons, canSave, extraConfig) {
    let container = this.getView();
    let child;
    try {
      child = Ext.create(Ext.apply({
        xtype: name,
        reference: name,
        flex: 1,
        minHeight: 240
      }, extraConfig || {}));
    } catch (error) {
      Ext.MessageBox.alert(
        'Cannot open response editor',
        (error && error.message) || String(error)
      );
      return;
    }
    this.getViewModel().set('currentViewReference', name);
    let previous = container.items.getRange();
    container.removeAll(false, true);
    try {
      container.add(child);
    } catch (addError) {
      Ext.Array.each(previous, function (item) {
        if (item && !item.destroyed) {
          container.add(item);
        }
      });
      child.destroy();
      Ext.MessageBox.alert(
        'Cannot open response editor',
        (addError && addError.message) || String(addError)
      );
      return;
    }
    Ext.Array.each(previous, function (item) {
      if (item && !item.destroyed) {
        item.destroy();
      }
    });

    this.syncPreviewActionFlags(name);
    Ext.ux.Mediator.fireEvent('parameterEditorController-updateActionButtons', actionButtons);
    Ext.ux.Mediator.fireEvent('parameterEditorController-canSaveButton', canSave);
    this.syncSelectorActionButtons(name);
    this.syncEditorSize();
    let win = container.up('window');
    if (container.updateLayout) {
      container.updateLayout();
    }
    if (win && !win.destroyed && win.updateLayout) {
      win.updateLayout();
    }
    this.syncEditorSize();
    if (win && !win.destroyed && yasmine.utils.ResponsiveUtil) {
      yasmine.utils.ResponsiveUtil.clampWindow(win);
    }
  },
  syncEditorSize: function () {
    let view = this.getView();
    let win = view && view.up('window');
    if (!view || view.destroyed || !win || win.destroyed || !win.body) {
      return;
    }
    let height = win.body.getHeight(true);
    let width = win.body.getWidth(true);
    if (height < 1 || width < 1) {
      return;
    }
    if (view.getWidth() === width && view.getHeight() === height) {
      return;
    }
    if (view.getHeight() < 80) {
      view.setHeight(height);
    }
    if (view.getWidth() < 80) {
      view.setWidth(width);
    }
    let child = view.items && view.items.getAt(0);
    if (child && !child.destroyed) {
      if (child.getHeight && child.getHeight() < 80 && child.setHeight) {
        child.setHeight(height);
      }
      if (child.updateLayout) {
        child.updateLayout();
      }
    }
  },
  syncPreviewActionFlags: function (viewName) {
    let win = this.getView() && this.getView().up('window');
    let vm = win && win.getViewModel();
    let preview = viewName === 'response-preview';
    if (!vm) {
      return;
    }
    vm.set({
      showResponseActions: true,
      showEditResponse: preview,
      showSelectResponse: preview,
      showRecalculateSensitivity: preview,
      showImportResp: preview
    });
  },
  onImportRespClick: function () {
    let field = this.lookupReference('respFileField');
    let input = field && (field.fileInputEl || (field.button && field.button.fileInputEl));
    if (input && input.dom) {
      input.dom.click();
    }
  },
  onRespFileChange: function (field) {
    if (!field || !field.getValue()) {
      return;
    }
    let form = this.lookupReference('respImportForm');
    let record = this.getViewModel().get('record');
    let nodeId = yasmine.utils.ResponseRecalculateUtil.nodeInstanceId(record);
    let that = this;
    form.getForm().submit({
      url: '/api/channel/response/import-resp/',
      params: {
        nodeInstanceId: nodeId
      },
      success: function (fp, action) {
        field.reset();
        that.applyImportedResponse(action.result || {});
      },
      failure: function (fp, action) {
        field.reset();
        let message = (action && action.result && action.result.message) || 'Cannot import RESP file';
        Ext.Msg.alert('Import RESP', message);
      }
    });
  },
  applyImportedResponse: function (result) {
    let vm = this.getViewModel();
    let record = vm.get('record');
    let nodeId = yasmine.utils.ResponseRecalculateUtil.nodeInstanceId(record);
    if (result.text) {
      vm.set('channelResponseText', result.text);
    }
    if (record && result.data) {
      if (result.id != null && result.id !== '') {
        record.set('id', result.id);
        record.phantom = false;
      }
      // Keep the record dirty so Save updates the stored Response.
      record.set('value', {
        nodeId: nodeId,
        response: result.data
      });
    }
    yasmine.utils.ResponseRecalculateUtil.clearPlotStageRange(vm);
    this.createPreview(true);
    this.loadChannelResponsePlot({stored: true});
    Ext.ux.Mediator.fireEvent('channel-response-imported', {
      nodeId: nodeId,
      text: result.text,
      data: result.data
    });
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
    var stacked = yasmine.utils.ResponsiveUtil.useStackLayout();
    return [
      Ext.create({
        xtype: 'button',
        text: stacked ? 'Edit' : 'Edit Response',
        tooltip: 'Edit Response',
        iconCls: 'x-fa fa-pencil',
        handler: () => this.createXmlResponseEditor()
      }),
      Ext.create({
        xtype: 'button',
        text: stacked ? 'Select' : 'Select a new Response',
        tooltip: 'Select a new Response',
        iconCls: 'x-fa fa-pencil',
        handler: () => this.createResponseSelector()
      }),
      this.createRecalculateSensitivityButton(stacked)
    ]
  },
  createTreeEditorActionButtons: function () {
    return [this.createRecalculateSensitivityButton()];
  },
  createRecalculateSensitivityButton: function (stacked) {
    return Ext.create({
      xtype: 'button',
      text: 'Recalculate Sensitivity',
      tooltip: 'Recalculate Sensitivity',
      iconCls: 'x-fa fa-calculator',
      handler: () => this.recalculateSensitivity()
    });
  },
  recalculateSensitivity: function (options) {
    options = options || {};
    let that = this;
    let vm = this.getViewModel();
    let record = vm && vm.get('record');
    if (!record) {
      return;
    }
    let nodeInstanceId = yasmine.utils.ResponseRecalculateUtil.nodeInstanceId(record);
    let currentViewRef = vm.get('currentViewReference');
    let payload = {
      nodeInstanceId: nodeInstanceId,
      min: vm.get('minFrequency'),
      max: vm.get('maxFrequency')
    };
    Ext.apply(payload, yasmine.utils.ResponseRecalculateUtil.plotStageParams(vm));

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

    let applyResult = function (result) {
      yasmine.utils.ResponseRecalculateUtil.setPlotLoading(that.getView(), false);
      if (!that.getView() || that.getView().destroyed) {
        return;
      }
      let viewModel = that.getViewModel();
      if (!viewModel) {
        return;
      }
      viewModel.set('channelResponseText', result.text);
      viewModel.set('channelResponseImageUrl', result.plot_url);
      viewModel.set('channelResponseCsvUrl', result.csv_url);
      yasmine.utils.ResponseRecalculateUtil.applyPlotMaxFrequency(viewModel, result);
      record.set('value', {
        nodeId: record.get('nodeId'),
        response: result.data
      });
      Ext.ux.Mediator.fireEvent('parameterEditorController-canSaveButton', true);

      if (currentViewRef === 'channel-response-tree-editor') {
        let treeView = that.lookup('channel-response-tree-editor') || that.getView().items.getAt(0);
        if (treeView && treeView.getController) {
          let treeController = treeView.getController();
          let tree = treeController.lookupReference('channelresponsetree');
          let selection = tree.getSelection()[0];
          if (!selection) {
            selection = tree.getStore().findNode(
              'key',
              'InstrumentSensitivity',
              tree.getStore().getRoot(),
              true,
              false,
              true
            );
          }
          let selectedPath = selection ?
            treeController.buildNodeIdentityPath(selection) : null;
          treeController.reloadTree(result.data, selectedPath);
        }
      }
    };

    if (options.prompt === false) {
      yasmine.utils.ResponseRecalculateUtil.setPlotLoading(this.getView(), true);
      yasmine.utils.ResponseRecalculateUtil.postRecalculateSensitivity(payload, null, {
        success: function (response) {
          yasmine.utils.ResponseRecalculateUtil.setPlotLoading(that.getView(), false);
          if (!that.getView() || that.getView().destroyed) {
            return;
          }
          let result = JSON.parse(response.responseText);
          if (!result.success) {
            yasmine.utils.ResponseRecalculateUtil.showRecalculateError(result.message);
            return;
          }
          applyResult(result);
        },
        failure: function () {
          yasmine.utils.ResponseRecalculateUtil.setPlotLoading(that.getView(), false);
          yasmine.utils.ResponseRecalculateUtil.showRecalculateError();
        }
      });
      return;
    }
    yasmine.utils.ResponseRecalculateUtil.promptRecalculateSensitivityWithReview(payload, {
      apply: applyResult,
      failure: function () {
        yasmine.utils.ResponseRecalculateUtil.showRecalculateError('Cannot load recalculation options.');
      }
    });
  },
  downloadChannelResponsePlot: function () {
    let url = this.getViewModel().get('channelResponseImageUrl');
    if (!url) {
      return;
    }
    let win = window.open(url, '_blank');
    if (win) {
      win.focus();
    }
  },
  downloadChannelResponseCsv: function () {
    let url = this.getViewModel().get('channelResponseCsvUrl');
    if (!url) {
      return;
    }
    let win = window.open(url, '_self');
    if (win) {
      win.focus();
    }
  },
  loadChannelResponsePlot: function (options) {
    options = options || {};
    let record = this.getViewModel().get('record');
    let pendingValue = record && record.get('value');
    if (!options.stored && pendingValue && pendingValue.response) {
      this.recalculateSensitivity({prompt: false});
      return;
    }

    let that = this;
    let view = this.getView();
    let nodeInstanceId = yasmine.utils.ResponseRecalculateUtil.nodeInstanceId(record);
    if (nodeInstanceId == null || nodeInstanceId === '') {
      return;
    }
    let min = this.getViewModel().get('minFrequency');
    let max = this.getViewModel().get('maxFrequency');
    let params = Ext.apply(
      {nodeInstanceId, min, max},
      yasmine.utils.ResponseRecalculateUtil.plotStageParams(this.getViewModel())
    );
    yasmine.utils.ResponseRecalculateUtil.setPlotLoading(view, true);
    Ext.Ajax.request({
      method: 'GET',
      params: params,
      url: `/api/channel/response/plot-url/`,
      success: function (response, options) {
        yasmine.utils.ResponseRecalculateUtil.setPlotLoading(view, false);
        if (!that.getView() || that.getView().destroyed) {
          return;
        }
        let vm = that.getViewModel();
        if (!vm) {
          return;
        }
        let result = JSON.parse(response.responseText);
        if (!result.success) {
          Ext.MessageBox.show({
            title: 'An error occurred',
            msg: result.message,
            buttons: Ext.MessageBox.OK,
            icon: Ext.MessageBox['ERROR'],
            width: 520
          });
        } else {
          vm.set('channelResponseImageUrl', result.plot_url);
          vm.set('channelResponseCsvUrl', result.csv_url);
          yasmine.utils.ResponseRecalculateUtil.applyPlotMaxFrequency(vm, result);
          var win = that.getView() && that.getView().up('window');
          if (win) {
            yasmine.utils.ResponsiveUtil.clampWindow(win);
          }
        }
      },
      failure: function () {
        yasmine.utils.ResponseRecalculateUtil.setPlotLoading(view, false);
        Ext.MessageBox.show({
          title: 'An error occurred',
          msg: 'Cannot load the response plot.',
          buttons: Ext.MessageBox.OK,
          icon: Ext.MessageBox['ERROR']
        });
      }
    });
  }
});

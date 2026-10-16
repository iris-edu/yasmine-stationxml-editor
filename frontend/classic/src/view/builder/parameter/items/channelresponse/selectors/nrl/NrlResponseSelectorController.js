/* ****************************************************************************
* 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
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
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.nrlselector.NrlResponseSelectorController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.nrl-response-selector',
  requires: ['yasmine.utils.ResponseRecalculateUtil'],
  isSingleElement: function () {
    let element = this.getViewModel() && this.getViewModel().get('responseElement');
    if (!element && this.getView().getResponseElement) {
      element = this.getView().getResponseElement();
    }
    return element === 'integrated' || element === 'soh';
  },

  init: function () {
    let me = this;
    this.getView().on('boxready', function () {
      if (!me.isSingleElement()) {
        return;
      }
      let sensorTab = me.getView().items.getAt(1);
      if (sensorTab && sensorTab.tab) {
        sensorTab.tab.hide();
      }
    });
  },

  initViewModel: function () {
    let element = this.getView().getResponseElement();
    if (element === 'integrated' || element === 'soh') {
      this.getViewModel().set('responseElement', element);
      let store = this.getStore('dataloggerStore');
      store.getProxy().setUrl('/api/nrl/' + element + '/');
      let root = store.getRoot();
      if (root) {
        root.set('text', element);
        if (root.set) {
          root.set('title', null);
        }
      }
      root.expand();
    } else {
      this.getStore('sensorStore').root.expand();
      this.getStore('dataloggerStore').root.expand();
    }
    this.syncActiveSelectorTab();
  },

  syncActiveSelectorTab: function () {
    let tabPanel = this.getView();
    let activeTab = tabPanel.getActiveTab();
    if (activeTab) {
      this.getViewModel().set('activeSelectorTab', tabPanel.items.indexOf(activeTab));
    }
  },

  onSelectorTabChange: function (tabPanel, newTab) {
    this.getViewModel().set('activeSelectorTab', tabPanel.items.indexOf(newTab));
    yasmine.utils.ResponseRecalculateUtil.updateWizardActionButtons(this.getViewModel());
    yasmine.utils.ResponseRecalculateUtil.updateParameterEditorActionButtons(this.getViewModel());
  },

  fillRecord: function () {
    let vm = this.getViewModel();
    let record = yasmine.utils.ResponseRecalculateUtil.getRecordFromContext(vm);
    if (!record) {
      return;
    }
    let sensorKeys = vm.get('sensorKeys');
    let dataloggerKeys = vm.get('dataloggerKeys');
    if (this.isSingleElement()) {
      if (!dataloggerKeys || !dataloggerKeys.length || !dataloggerKeys[0]) {
        return;
      }
      let value = {
        libraryType: 'nrl',
        nrlResponseType: vm.get('responseElement'),
        sensorKeys: dataloggerKeys,
        dataloggerKeys: []
      };
      record.set('value', yasmine.utils.ResponseRecalculateUtil.withRecalculateFlag(value, vm));
      return;
    }
    if (!sensorKeys || !dataloggerKeys) {
      return;
    }

    let value = { libraryType: 'nrl', sensorKeys, dataloggerKeys };
    record.set('value', yasmine.utils.ResponseRecalculateUtil.withRecalculateFlag(value, vm));
  },
  isDataloggerCompleted: function () {
    return !!this.getViewModel().get('dataloggerPreview');
  },
  isSensorCompleted: function () {
    if (this.isSingleElement()) {
      return true;
    }
    return !!this.getViewModel().get('sensorPreview');
  },
  onSensorSelectionChange: function (cmp, node) {
    this.showResponse(node, 'sensor', 'sensorKeys');
  },
  onSensorClick: function (item) {
    let node = this.getStore('sensorStore').getNodeById(item._breadcrumbNodeId);
    this.showResponse(node, 'sensor', 'sensorKeys');
  },
  onDataloggerSelectionChange: function (cmp, node) {
    this.showResponse(node, 'datalogger', 'dataloggerKeys');
  },
  onDataloggerClick: function (item) {
    let node = this.getStore('dataloggerStore').getNodeById(item._breadcrumbNodeId);
    this.showResponse(node, 'datalogger', 'dataloggerKeys');
  },
  getSelectedDataloggerKeys: function () {
    if (this.isSingleElement()) {
      return [];
    }
    return this.getViewModel().get('dataloggerKeys');
  },
  getSelectedSensorKeys: function () {
    if (this.isSingleElement()) {
      return this.getViewModel().get('dataloggerKeys') || [];
    }
    return this.getViewModel().get('sensorKeys');
  },
  loadChannelResponsePlot: function () {
    if (this.getViewModel().get('responseTree')) {
      this.recalculateSensitivity({prompt: false});
      return;
    }
    this.loadChannelResponseIfPossible();
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
  showResponse: function (node, device, keysProperty) {
    this.getViewModel().set(`${device}Preview`, null);
    this.getViewModel().set('channelResponseText', null);
    this.getViewModel().set('channelResponseImageUrl', null);
    this.getViewModel().set('channelResponseCsvUrl', null);
    this.getViewModel().set('responseTree', null);
    this.getViewModel().set(keysProperty, null);
    if (!node || !node.isLeaf() || !node.get('key')) {
      Ext.ux.Mediator.fireEvent('parameterEditorController-canSaveButton', false);
      yasmine.utils.ResponseRecalculateUtil.updateWizardActionButtons(this.getViewModel());
      yasmine.utils.ResponseRecalculateUtil.updateParameterEditorActionButtons(this.getViewModel());
      return;
    }
    this.setKeys(node, keysProperty);
    this.loadPreviewResponse(device, this.getViewModel().get(keysProperty));
  },
  loadPreviewResponse: function (device, keys) {
    let that = this;
    Ext.Ajax.request({
      method: 'GET',
      params: {keys},
      url: this.isSingleElement()
        ? '/api/nrl/' + this.getViewModel().get('responseElement') + '/response/'
        : '/api/nrl/' + device + '/response/',
      success: function (response) {
        that.getViewModel().set(`${device}Preview`, response.responseText);
        that.loadChannelResponseIfPossible();
      },
      failure: function (response) {
        that.getViewModel().set('preview', response.status);
      }
    });
  },
  loadChannelResponseIfPossible: function () {
    let sensorKeys = this.getViewModel().get('sensorKeys');
    let dataloggerKeys = this.getViewModel().get('dataloggerKeys');
    let single = this.isSingleElement();
    if (single) {
      sensorKeys = dataloggerKeys;
      if (!sensorKeys || sensorKeys.length === 0 || !sensorKeys[0]) {
        return;
      }
    } else {
      if (!sensorKeys || sensorKeys.length === 0) {
        return;
      }
      if (!dataloggerKeys || dataloggerKeys.length === 0) {
        return;
      }
    }
    let min = this.getViewModel().get('minFrequency');
    let max = this.getViewModel().get('maxFrequency');
    let that = this;
    let element = this.getViewModel().get('responseElement');
    let stageParams = yasmine.utils.ResponseRecalculateUtil.plotStageParams(this.getViewModel());
    yasmine.utils.ResponseRecalculateUtil.setPlotLoading(this.getView(), true);
    Ext.Ajax.request({
      method: 'GET',
      params: Ext.apply(
        single
          ? {keys: sensorKeys, min, max}
          : {sensorKeys, dataloggerKeys, min, max},
        stageParams
      ),
      url: single
        ? '/api/nrl/' + element + '/response/preview/'
        : '/api/nrl/channel/response/preview/',
      success: function (response, options) {
        yasmine.utils.ResponseRecalculateUtil.setPlotLoading(that.getView(), false);
        let result = JSON.parse(response.responseText);
        that.getViewModel().set('channelResponseText', result.text);
        Ext.ux.Mediator.fireEvent('parameterEditorController-canSaveButton', true);
        that.getViewModel().set('channelResponseImageUrl', result.plot_url || null);
        that.getViewModel().set('channelResponseCsvUrl', result.csv_url || null);
        yasmine.utils.ResponseRecalculateUtil.applyPlotMaxFrequency(that.getViewModel(), result);
        if (!result.success) {
          that.getViewModel().set('channelResponseImageUrl', null);
          that.getViewModel().set('channelResponseCsvUrl', null);
          Ext.MessageBox.show({
            title: 'An error occurred',
            msg: result.message,
            buttons: Ext.MessageBox.OK,
            icon: Ext.MessageBox.ERROR
          });
        } else if (result.plot_failed && result.message) {
          that.getViewModel().set('channelResponseImageUrl', null);
          that.getViewModel().set('channelResponseCsvUrl', null);
          Ext.MessageBox.show({
            title: 'Plot unavailable',
            msg: result.message,
            buttons: Ext.MessageBox.OK,
            icon: Ext.MessageBox.WARNING
          });
        }
        yasmine.utils.ResponseRecalculateUtil.updateWizardActionButtons(that.getViewModel());
        yasmine.utils.ResponseRecalculateUtil.updateParameterEditorActionButtons(that.getViewModel());
      },
      failure: function () {
        yasmine.utils.ResponseRecalculateUtil.setPlotLoading(that.getView(), false);
      }
    });
  },
  setKeys: function (node, device) {
    let keys = [];
    this.buildKeys(node, keys);
    this.getViewModel().set(device, keys);
  },
  buildKeys: function (node, result) {
    if (!node) {
      return [];
    }
    result.push(node.get('key'));

    if (node.parentNode) {
      this.buildKeys(node.parentNode, result);
    } else {
      result = result.reverse();
      result = result.shift();
    }
  },

  recalculateSensitivity: function (options) {
    options = options || {};
    let vm = this.getViewModel();
    let sensorKeys = vm.get('sensorKeys');
    let dataloggerKeys = vm.get('dataloggerKeys');
    let single = this.isSingleElement();
    if (single) {
      sensorKeys = dataloggerKeys;
      if (!sensorKeys || !sensorKeys.length || !sensorKeys[0]) {
        return;
      }
    } else if (!sensorKeys || !sensorKeys.length || !dataloggerKeys || !dataloggerKeys.length) {
      return;
    }
    let payload = {
      libraryType: 'nrl',
      sensorKeys: sensorKeys,
      dataloggerKeys: single ? [] : dataloggerKeys,
      min: vm.get('minFrequency'),
      max: vm.get('maxFrequency')
    };
    Ext.apply(payload, yasmine.utils.ResponseRecalculateUtil.plotStageParams(vm));
    if (single) {
      payload.nrlResponseType = vm.get('responseElement');
    }
    let handlers = {
      apply: function (result) {
        yasmine.utils.ResponseRecalculateUtil.applyRecalculateResult(vm, result);
      },
      success: function (response) {
        let result = JSON.parse(response.responseText);
        if (!result.success) {
          yasmine.utils.ResponseRecalculateUtil.showRecalculateError(result.message);
          return;
        }
        yasmine.utils.ResponseRecalculateUtil.applyRecalculateResult(vm, result);
      },
      failure: function () {
        yasmine.utils.ResponseRecalculateUtil.showRecalculateError();
      }
    };
    if (options.prompt === false) {
      yasmine.utils.ResponseRecalculateUtil.postRecalculateSensitivity(
        payload, null, handlers
      );
      return;
    }
    yasmine.utils.ResponseRecalculateUtil.promptRecalculateSensitivityWithReview(payload, {
      apply: handlers.apply,
      failure: function () {
        yasmine.utils.ResponseRecalculateUtil.showRecalculateError('Cannot load recalculation options.');
      }
    });
  }
});

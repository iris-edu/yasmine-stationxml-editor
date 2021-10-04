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


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.nrlselector.NrlResponseSelectorController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.nrl-response-selector',
  initViewModel: function () {
    this.getStore('sensorStore').root.expand();
    this.getStore('dataloggerStore').root.expand();
  },
  fillRecord: function () {
    let sensorKeys = this.getViewModel().get('sensorKeys');
    let dataloggerKeys = this.getViewModel().get('dataloggerKeys');
    if (!sensorKeys || !dataloggerKeys) {
      return;
    }

    let record = this.getViewModel().get('record');
    record.set('value', {libraryType: 'nrl', sensorKeys, dataloggerKeys});
  },
  isDataloggerCompleted: function () {
    return !!this.getViewModel().get('dataloggerPreview');
  },
  isSensorCompleted: function () {
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
    return this.getViewModel().get('dataloggerKeys');
  },
  getSelectedSensorKeys: function () {
    return this.getViewModel().get('sensorKeys');
  },
  loadChannelResponsePlot: function () {
    this.loadChannelResponseIfPossible();
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
  showResponse: function (node, device, keysProperty) {
    this.getViewModel().set(`${device}Preview`, null);
    this.getViewModel().set('channelResponseText', null);
    this.getViewModel().set('channelResponseImageUrl', null);
    this.getViewModel().set('channelResponseCsvUrl', null);
    this.getViewModel().set(keysProperty, null);
    if (!node.isLeaf()) {
      Ext.ux.Mediator.fireEvent('parameterEditorController-canSaveButton', false);
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
      url: `/api/nrl/${device}/response/`,
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
    if (!sensorKeys || sensorKeys.length === 0) {
      return;
    }
    let dataloggerKeys = this.getViewModel().get('dataloggerKeys');
    if (!dataloggerKeys || dataloggerKeys.length === 0) {
      return;
    }
    let min = this.getViewModel().get('minFrequency');
    let max = this.getViewModel().get('maxFrequency');
    let that = this;
    Ext.Ajax.request({
      method: 'GET',
      params: {sensorKeys, dataloggerKeys, min, max},
      url: `/api/nrl/channel/response/preview/`,
      success: function (response, options) {
        let result = JSON.parse(response.responseText);
        that.getViewModel().set('channelResponseText', result.text);
        Ext.ux.Mediator.fireEvent('parameterEditorController-canSaveButton', true);
        that.getViewModel().set('channelResponseImageUrl', result.plot_url);
        that.getViewModel().set('channelResponseCsvUrl', result.csv_url);
        if (!result.success || result.message) {
          that.getViewModel().set('channelResponseImageUrl', null);
          that.getViewModel().set('channelResponseCsvUrl', null);
          Ext.MessageBox.show({
            title: 'An error occurred',
            msg: result.message,
            buttons: Ext.MessageBox.OK,
            icon: Ext.MessageBox['ERROR']
          });
        }
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
  }
});

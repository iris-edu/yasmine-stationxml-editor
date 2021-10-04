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


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.ChannelResponseEditorController', {
  extend: 'yasmine.view.xml.builder.parameter.ParameterItemEditorController',
  alias: 'controller.channel-response-editor',
  requires: [
    'Ext.ux.Mediator',
    'yasmine.view.xml.builder.parameter.items.channelresponse.preview.ResponsePreview',
    'yasmine.view.xml.builder.parameter.items.channelresponse.selectors.SelectorsContainer',
    'yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.ChannelResponseTreeEditor',
    'yasmine.view.xml.builder.parameter.items.channelresponse.nrl.NrlResponseSelector',
    'yasmine.view.xml.builder.parameter.items.channelresponse.arol.ArolResponseSelector'
  ],
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
    let currentViewController = this.lookup(currentViewRef).getController();
    currentViewController.fillRecord();
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
  createXmlResponseEditor: function () {
    this.createComponent('channel-response-tree-editor', [], true);
  },
  createComponent(name, actionButtons, canSave) {
    this.getViewModel().set('currentViewReference', name);
    let container = this.getView();
    container.removeAll(true, true);
    container.add(Ext.create({xtype: name}));

    Ext.ux.Mediator.fireEvent('parameterEditorController-updateActionButtons', actionButtons);
    Ext.ux.Mediator.fireEvent('parameterEditorController-canSaveButton', canSave);
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
      })
    ]
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
    let that = this;
    let record = this.getViewModel().get('record');
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

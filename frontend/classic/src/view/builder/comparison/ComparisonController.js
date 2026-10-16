/* ****************************************************************************
* 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
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
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.comparison.ComparisonController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.comparison',
  requires: ['yasmine.utils.ResponseRecalculateUtil'],
  init: function () {
    this.mon(Ext.ux.Mediator, 'node-selected', this.onXml1NodeSelected, this);
    this.mon(Ext.GlobalEvents, 'resize', this.syncComparisonSplit, this, {buffer: 200});
    this.configureComparisonCharts();
  },
  configureComparisonCharts: function () {
    var names = ['xml1Chart', 'xml2Chart', 'xml3Chart'];
    var i, chart, chartModel;
    for (i = 0; i < names.length; i++) {
      chart = this.lookup(names[i]);
      chartModel = chart && chart.getViewModel && chart.getViewModel();
      if (!chartModel) {
        continue;
      }
      chartModel.set('showChartControls', false);
      chartModel.set('showDownloadButtons', false);
      // chartImageHtml does not publish until every get() dependency has a
      // value. plotLoading is set by the response editor, not by Compare.
      chartModel.set('plotLoading', false);
      chartModel.set('channelResponsePlotMessage', null);
      if (chartModel.notify) {
        chartModel.notify();
      }
    }
  },
  syncComparisonSplit: function () {
    var view = this.getView();
    yasmine.utils.ResponsiveUtil.applyComparisonSplit(this.lookup('comparisonSplit'));
    if (this.isAlive() && view.rendered && view.updateLayout) {
      view.updateLayout();
    }
  },
  _getNodeData: function (node) {
    if (!node) {
      return null;
    }
    return (typeof node.getData === 'function') ? node.getData() : node;
  },
  initData: function (node) {
    this.onXml1NodeSelected(this._getNodeData(node));
  },
  isAlive: function () {
    var view = this.getView();
    return !!(view && !view.destroyed && this.getViewModel());
  },
  onXml2Select: function (cmp, record) {
    if (!this.isAlive()) {
      return;
    }
    this.getViewModel().set('xml2Id', record.get('id'));
    this.loadXml2ChannelResponsePlotIfPossible();
  },
  onXml1NodeSelected: function (item) {
    item = this._getNodeData(item);
    if (!item || item.nodeType !== yasmine.NodeTypeEnum.channel) {
      return;
    }
    yasmine.services.NodeService.findNodePath(item.id).then(x => {
      if (!this.isAlive()) {
        return;
      }
      let stationCode = x.path[1].code;
      let channelCode = item.code;
      let channelLocationCode = item.location_code;
      this.getViewModel().set('xml1ChannelTitle', `${stationCode} / ${channelLocationCode}.${channelCode}`);
      this.getViewModel().set('xml1NodeInstanceId', item.id);
      this.rebuildPlots();
    });
  },
  rebuildPlots: function() {
    this.setPlotsUrl('xml1Chart', null);
    this.setPlotsUrl('xml2Chart', null);
    this.setPlotsUrl('xml3Chart', null);
    this.loadXml1ChannelResponsePlotIfPossible();
    this.loadXml2ChannelResponsePlotIfPossible();
  },
  loadXml1ChannelResponsePlotIfPossible: function () {
    if (!this.isAlive()) {
      return;
    }
    let xml1NodeInstanceId = this.getViewModel().get('xml1NodeInstanceId');
    if (!xml1NodeInstanceId) {
      return;
    }
    this.setLoading('xml1Chart', true);
    yasmine.services.NodeService.loadNodeAttributes(xml1NodeInstanceId).then((attributes) => {
      if (!this.isAlive()) {
        return;
      }
      this.setLoading('xml1Chart', false);
      if (attributes.findIndex(x => x['attr_name'] === 'response') > -1) {
        this.loadChannelResponsePlot(xml1NodeInstanceId, 'xml1Chart');
      }
    })
  },
  loadXml2ChannelResponsePlotIfPossible: function () {
    if (!this.isAlive()) {
      return;
    }
    let xml2Id = this.getViewModel().get('xml2Id');
    if (!xml2Id) {
      return;
    }

    let xml2NodeInstanceId = this.getViewModel().get('xml1NodeInstanceId');
    if (!xml2NodeInstanceId) {
      return;
    }

    this.setLoading('xml2Chart', true);
    yasmine.services.NodeService.findSimilarChannel(xml2Id, xml2NodeInstanceId).then((data) => {
      if (!this.isAlive()) {
        return;
      }
      this.setLoading('xml2Chart', false);
      this.setPlotsUrl('xml2Chart', null);
      this.getViewModel().set('xml2NodeInstanceId', null);
      this.getViewModel().set('xml2ChannelTitle', 'N/A');
      if (data.nodeInstanceId) {
        this.getViewModel().set('xml2NodeInstanceId', data.nodeInstanceId);
        this.getViewModel().set('xml2ChannelTitle', this.getViewModel().get('xml1ChannelTitle'));
      }
      if (data.nodeInstanceId && data.hasResponse) {
        this.loadChannelResponsePlot(data.nodeInstanceId, 'xml2Chart');
        this.loadChannelResponsePlotDifference();
      }
    });
  },
  loadChannelResponsePlotDifference: function () {
    this.setLoading('xml3Chart', true);
    let max = this.getViewModel().get('maxFrequency');
    let min = this.getViewModel().get('minFrequency');
    let xml1NodeId = this.getViewModel().get('xml1NodeInstanceId');
    let xml2NodeId = this.getViewModel().get('xml2NodeInstanceId');
    yasmine.services.ChannelPlotService.loadPlotDifference(xml1NodeId, xml2NodeId, max, min).then((url) => {
      if (!this.isAlive()) {
        return;
      }
      this.setLoading('xml3Chart', false);
      this.setPlotsUrl('xml3Chart', url);
    });
  },
  downloadChannelResponsePlot: function () {
    // let win = window.open('', '_blank');
    // win.location = this.getViewModel().get('channelResponseImageUrl');
    // win.focus();
  },
  downloadChannelResponseCsv: function () {
    // let win = window.open('', '_self');
    // win.location = this.getViewModel().get('channelResponseCsvUrl');
    // win.focus();
  },
  loadChannelResponsePlot: function (nodeInstanceId, chartCmpName) {
    let max = this.getViewModel().get('maxFrequency');
    let min = this.getViewModel().get('minFrequency');
    this.setLoading(chartCmpName, true);
    yasmine.services.ChannelPlotService.loadPlot(nodeInstanceId, max, min).then((result) => {
      if (!this.isAlive()) {
        return;
      }
      this.setLoading(chartCmpName, false);
      this.setPlotsUrl(chartCmpName, result.plot_url);
      this.setPlotsCsv(chartCmpName, result.csv_url);
      yasmine.utils.ResponseRecalculateUtil.applyPlotMaxFrequency(this.getViewModel(), result);
    });
  },
  setPlotsUrl: function (cmpName, url) {
    let chart = this.lookup(cmpName);
    let chartModel = chart && chart.getViewModel && chart.getViewModel();
    if (!this.isAlive() || !chartModel) {
      return;
    }
    chartModel.set('channelResponseImageUrl', url);
    if (chartModel.notify) {
      chartModel.notify();
    }
    this.getViewModel().set(`${cmpName}ChannelResponseImageUrl`, url);
    if (this.getViewModel().notify) {
      this.getViewModel().notify();
    }
    this.syncComparisonSplit();
  },
  setPlotsCsv: function (cmpName, csv) {
    let chart = this.lookup(cmpName);
    let chartModel = chart && chart.getViewModel && chart.getViewModel();
    if (!this.isAlive() || !chartModel) {
      return;
    }
    chartModel.set('channelResponseCsvUrl', csv);
    this.getViewModel().set(`${cmpName}ChannelResponseCsvUrl`, csv);
  },
  setLoading: function (cmpName, value) {
    if (!this.isAlive()) {
      return;
    }
    this.getViewModel().set(`${cmpName}IsLoading`, value);
  }
});

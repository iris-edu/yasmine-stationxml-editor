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
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.comparison.ComparisonController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.comparison',
  init: function () {
    Ext.ux.Mediator.on('node-selected', this.onXml1NodeSelected, this);
  },
  initData: function (node) {
    if (node.getData().nodeType !== yasmine.NodeTypeEnum.channel) {
      return;
    }
    this.onXml1NodeSelected(node);
  },
  onXml2Select: function (cmp, record) {
    this.getViewModel().set('xml2Id', record.get('id'));
    this.loadXml2ChannelResponsePlotIfPossible();
  },
  onXml1NodeSelected: function (item) {
    if (item.nodeType !== yasmine.NodeTypeEnum.channel) {
      return;
    }
    yasmine.services.NodeService.findNodePath(item.id).then(x => {
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
    let xml1NodeInstanceId = this.getViewModel().get('xml1NodeInstanceId');
    if (!xml1NodeInstanceId) {
      return;
    }
    this.setLoading('xml1Chart', true);
    yasmine.services.NodeService.loadNodeAttributes(xml1NodeInstanceId).then((attributes) => {
      this.setLoading('xml1Chart', false);
      if (attributes.findIndex(x => x['attr_name'] === 'response') > -1) {
        this.loadChannelResponsePlot(xml1NodeInstanceId, 'xml1Chart');
      }
    })
  },
  loadXml2ChannelResponsePlotIfPossible: function () {
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
      this.setLoading(chartCmpName, false);
      this.setPlotsUrl(chartCmpName, result.plot_url);
      this.setPlotsCsv(chartCmpName, result.csv_url);
    });
  },
  setPlotsUrl: function (cmpName, url) {
    let chartModel = this.lookup(cmpName).getViewModel();
    chartModel.set('channelResponseImageUrl', url);
    this.getViewModel().set(`${cmpName}ChannelResponseImageUrl`, url);
  },
  setPlotsCsv: function (cmpName, csv) {
    let chartModel = this.lookup(cmpName).getViewModel();
    chartModel.set('channelResponseCsvUrl', csv);
    this.getViewModel().set(`${cmpName}ChannelResponseCsvUrl`, csv);
  },
  setLoading: function (cmpName, value) {
    this.getViewModel().set(`${cmpName}IsLoading`, value);
  }
});

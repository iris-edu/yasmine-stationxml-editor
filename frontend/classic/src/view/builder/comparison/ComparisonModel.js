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


Ext.define('yasmine.view.xml.builder.comparison.ComparisonModel', {
  extend: 'Ext.app.ViewModel',
  alias: 'viewmodel.comparison',
  data: {
    xml1ChartIsLoading: false,
    xml2ChartIsLoading: false,
    xml3ChartIsLoading: false,
    xml1ChannelTitle: 'N/A',
    xml2ChannelTitle: 'N/A',
    xml1NodeInstanceId: null,
    xml2NodeInstanceId: null,
    xml1ChartChannelResponseImageUrl: null,
    xml2ChartChannelResponseImageUrl: null,
    xml2Id: null,
    xml3Id: null,
    minFrequency: 0.001,
    maxFrequency: null
  },
  stores: {
    xmlStore: {
      model: 'yasmine.model.Xml',
      autoLoad: true,
      remoteFilter: false,
      remoteSort: false,
      autoSync: false,
      pageSize: 0,
      sorters: [{
        property: 'name',
        direction: 'ASC'
      }],
    }
  },
  formulas: {
    xml1ChartMessage: function (get) {
      if (get('xml1ChartIsLoading')) {
        return 'Loading ...';
      }
      if (!get('xml1NodeInstanceId')) {
        return 'Please select a channel!';
      }
      if (!get('xml1ChartChannelResponseImageUrl')) {
        return 'Selected channel doesn\'t have a response.';
      }
    },
    xml2ChartMessage: function (get) {
      if (!get('xml2Id')) {
        return 'Please select an XML!'
      }
      if (get('xml2ChartIsLoading')) {
        return 'Loading ...';
      }
      if (!get('xml1NodeInstanceId')) {
        return 'Please select a channel!'
      }
      if (!get('xml2NodeInstanceId')) {
        return 'Cannot find a similar channel.'
      }
      if (!get('xml2ChartChannelResponseImageUrl')) {
        return 'Channel was found, but it doesn\'t have a response.'
      }
    },
    xml3ChartMessage: function (get) {
      if (get('xml3ChartIsLoading')) {
        return 'Loading ...';
      }
      if (!get('xml1ChartChannelResponseImageUrl') || !get('xml2ChartChannelResponseImageUrl')) {
        return 'Both responses should be selected to see their difference here.'
      }
    }
  }
});

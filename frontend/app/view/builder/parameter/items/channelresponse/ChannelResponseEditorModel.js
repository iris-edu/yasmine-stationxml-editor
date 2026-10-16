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


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.ChannelResponseEditorModel', {
  extend: 'yasmine.view.xml.builder.parameter.ParameterItemEditorModel',
  alias: 'viewmodel.channel-response-editor',
  data: {
    currentViewReference: null,
    settingsUpdatedAt: 0,
    channelResponseImageUrl: null,
    channelResponseText: null,
    channelResponsePlotMessage: null,
    minFrequency: 0.001,
    maxFrequency: null,
    plotStartStage: null,
    plotEndStage: null,
    hasPlotStages: false,
    plotLoading: false
  },
  stores: {
    plotStageStore: {
      fields: ['number', 'label'],
      data: []
    }
  },
  formulas: {
    nrlv2OnlineEnabled: function (get) {
      get('settingsUpdatedAt'); // dependency: re-evaluate when settings are saved
      let s = yasmine.Globals.Settings;
      if (!s) return false;
      let val = (typeof s.get === 'function') ? s.get('nrlv2__nrlv2_online_enabled') : s['nrlv2__nrlv2_online_enabled'];
      return !!val;
    },
    nrlv2OnlineTooltip: function (get) {
      return get('nrlv2OnlineEnabled') ? '' : 'Enable in Settings';
    }
  }
});

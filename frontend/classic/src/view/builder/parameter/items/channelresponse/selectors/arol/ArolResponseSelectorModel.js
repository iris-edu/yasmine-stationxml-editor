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


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.arolselector.ArolResponseSelectorModel', {
  extend: 'Ext.app.ViewModel',
  alias: 'viewmodel.arol-response-selector',
  data: {
    debugMode: false,

    dataloggerCompleted: false,
    sensorCompleted: false,
    channelResponseText: null,
    channelResponseImageUrl: null,
    channelResponseCsvUrl: null,

    wizardMode: false,
    responseTree: null,
    activeSelectorTab: 0,

    dataloggerPreview: '',
    sensorPreview: '',

    minFrequency: 0.001,
    maxFrequency: null,

    datalogger: {
      keys: null,
      selectedOptions: new Map(),
      selectedFiles: [],
      completed: false,
      availableFilterGroups: null,
      resultTitle: null
    },
    sensor: {
      keys: null,
      selectedOptions: new Map(),
      selectedFiles: [],
      completed: false,
      availableFilterGroups: null,
      resultTitle: null
    },

    datalogger_file: '',
    sensor_file: '',
  },
  formulas: {
    dataloggerStatus: function (get) {
      return (get('dataloggerCompleted'))
        ? ' <i class="fa fa-check arol-status-icon"></i>'
        : ' <i class="fa fa-ban arol-status-icon"></i>';
    },
    sensorStatus: function (get) {
      return (get('sensorCompleted'))
        ? ' <i class="fa fa-check arol-status-icon"></i>'
        : ' <i class="fa fa-ban arol-status-icon"></i>';
    },
    responseStatus: function (get) {
      return (get('dataloggerCompleted') && get('sensorCompleted'))
        ? ' <i class="fa fa-check arol-status-icon"></i>'
        : ' <i class="fa fa-ban arol-status-icon"></i>';
    },
    responsePreviewWizardCls: function (get) {
      return get('wizardMode') ? 'response-preview-wizard' : '';
    },
    dataloggerResultTitle: function (get) {
      return get('dataloggerCompleted') ? `<b>${get('datalogger').resultTitle}</b>` : '';
    },
    sensorResultTitle: function (get) {
      return get('sensorCompleted') ? `<b>${get('sensor').resultTitle}</b>` : '';
    },
    dataloggerResponseTitle: function (get) {
      return get('dataloggerCompleted')
        ? 'Datalogger has been selected'
        : 'Please select datalogger';
    },
    sensorResponseTitle: function (get) {
      return get('sensorCompleted')
        ? 'Sensor has been selected'
        : 'Please select sensor';
    }
  }
});

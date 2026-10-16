/* ****************************************************************************
* 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
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


Ext.define('yasmine.view.xml.builder.wizard.WizardCreateModel', {
  extend: 'Ext.app.ViewModel',
  alias: 'viewmodel.wizard-create',
  data: {
    xmlId: null,
    startNodeId: null,
    startNodeType: null,
    startIndex: 0,
    currentIndex: 0,
    finishIndex: 3,
    channelStoredData: {
      channelInfos: []
    },
    stationStoredData: {
      activeSampleRate: 1,
      attributes: []
    },
    networkStoredData: {
      attributes: []
    },
    finalStepStoreData: {
      network: false,
      station: false,
      channel: false,
      userLibraryId: null
    }
  },
  formulas: {
    currentTitle: function (get) {
      let steps = {
        0: 'Network',
        1: 'Station',
        2: 'Channel',
        3: 'Final Step'
      };
      let result = [];
      for (let i = get('startIndex'); i <= get('finishIndex'); i++) {
        if (i === get('currentIndex')) {
          result.push(steps[i].toUpperCase());
        } else {
          result.push(steps[i]);
        }
      }
      return result.join(' > ');
    },
    hasNext: function (get) {
      return get('currentIndex') < get('finishIndex');
    },
    hasPrevious: function (get) {
      return get('currentIndex') > get('startIndex');
    }
  }
});

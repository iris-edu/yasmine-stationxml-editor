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
* 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.wizard.channelsteps.steps.WizardCreateChannelModel', {
  extend: 'Ext.app.ViewModel',
  alias: 'viewmodel.wizard-create-channel-item',
  data: {
    settingsUpdatedAt: 0,
    channelInfo: null,
    activeIndex: 0,
    totalSteps: 0,
    sampleRateNumber: 1,
    multiSampleRate: false,
    stationAttributes: [],
    codePrefix: null,
    orient: null,
    sohMode: false,
    integratedMode: false,
    orientationApplies: null,
    sohChannelCode: null,
    sohSuggestedPrefix: null,
    sohSuggestedCode: null,
    scalarChannel: false,
    sampleRateKnown: true,
    resolvedSampleRate: null,

    selectedLibrary: null,
    nrlResponseType: null,
    stepsStoredData: {
      selectedLibrary: null,
      nrlResponseType: null,
      dataloggerKeys: [],
      sensorKeys: []
    },

    hasNextStep: false,
    hasPreviousStep: false,
    isCompleted: false,
    completionStatusLabel: null
  },
  formulas: {
    asksOrientation: function (get) {
      return !!get('sohMode') || !!get('integratedMode');
    },
    orientIsZ: function (get) {
      if (get('scalarChannel')) {
        return true;
      }
      if (get('asksOrientation') && get('orientationApplies') === false) {
        return true;
      }
      return get('orient') === yasmine.ChannelOrient.Z;
    },
    showSohQuestion: function (get) {
      return get('asksOrientation');
    },
    showOrientedCode: function (get) {
      if (get('scalarChannel')) {
        return false;
      }
      return !get('asksOrientation') || get('orientationApplies') === true;
    },
    showSohName: function (get) {
      return !!get('scalarChannel') || (get('asksOrientation') && get('orientationApplies') === false);
    },
    hideDipAzimuth: function (get) {
      return !!get('scalarChannel') || (get('asksOrientation') && get('orientationApplies') === false);
    },
    nrlv2OnlineEnabled: function (get) {
      get('settingsUpdatedAt'); // dependency: re-evaluate when settings are saved
      let s = yasmine.Globals.Settings;
      if (!s) return false;
      let val = (typeof s.get === 'function') ? s.get('nrlv2__nrlv2_online_enabled') : s['nrlv2__nrlv2_online_enabled'];
      return !!val;
    },
    nrlv2OnlineTooltip: function (get) {
      return get('nrlv2OnlineEnabled') ? '' : 'Enable in Settings';
    },
    nrlLibrarySelected: function (get) {
      let lib = get('selectedLibrary');
      // Before a library is chosen, keep the NRL type step in the count so
      // "Step X of Y" does not jump from 5 to 6 after picking NRL.
      return !lib || lib === 'nrl' || lib === 'nrlv2_online';
    },
    panelTitle: function (get) {
      let label = get('completionStatusLabel') || '';
      if (get('multiSampleRate')) {
        return label + ' Sample Rate #' + get('sampleRateNumber');
      }
      return label + ' Channel';
    },
    locationStepNumber: function () {
      return 1;
    },
    libraryStepNumber: function () {
      return 2;
    },
    typeStepNumber: function () {
      return 3;
    },
    selectorStepNumber: function (get) {
      return get('nrlLibrarySelected') ? 4 : 3;
    },
    codeStepNumber: function (get) {
      return get('nrlLibrarySelected') ? 5 : 4;
    },
    detailStepNumber: function (get) {
      return get('nrlLibrarySelected') ? 6 : 5;
    },
    visibleStepCount: function (get) {
      let count = get('nrlLibrarySelected') ? 6 : 5;
      if (get('hideDipAzimuth')) {
        count -= 1;
      }
      return count;
    },
    stepHeadingPrefix: function (get) {
      if (get('multiSampleRate')) {
        return 'Sample Rate #' + get('sampleRateNumber') + ' · ';
      }
      return '';
    },
    locationStepHeading: function (get) {
      return get('stepHeadingPrefix') + 'Location / Step ' + get('locationStepNumber') + ' of ' + get('visibleStepCount');
    },
    libraryStepHeading: function (get) {
      return get('stepHeadingPrefix') + 'Response library / Step ' + get('libraryStepNumber') + ' of ' + get('visibleStepCount');
    },
    typeStepHeading: function (get) {
      return get('stepHeadingPrefix') + 'Response type / Step ' + get('typeStepNumber') + ' of ' + get('visibleStepCount');
    },
    selectorStepHeading: function (get) {
      return get('stepHeadingPrefix') + 'Instrument configuration / Step ' + get('selectorStepNumber') + ' of ' + get('visibleStepCount');
    },
    codeStepHeading: function (get) {
      let title = get('asksOrientation') ? 'Orientation & channel code' : 'Channel code';
      return get('stepHeadingPrefix') + title + ' / Step ' + get('codeStepNumber') + ' of ' + get('visibleStepCount');
    },
    detailStepHeading: function (get) {
      return get('stepHeadingPrefix') + 'Channel details / Step ' + get('detailStepNumber') + ' of ' + get('visibleStepCount');
    }
  }
});

/* ****************************************************************************
* 2026-09-27, version 4.4.0-beta: ASGSR, Alexey Emanov
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


Ext.define('yasmine.view.xml.builder.wizard.channelsteps.steps.Step4View', {
  extend: 'Ext.panel.Panel',
  xtype: 'channel-step-4',
  controller: {
    isValid: function () {
      let viewModel = this.getViewModel();
      if (viewModel.get('asksOrientation') && viewModel.get('orientationApplies') !== true && viewModel.get('orientationApplies') !== false) {
        Ext.Msg.alert('Error', 'Please choose whether orientation applies to this channel', Ext.emptyFn);
        return false;
      }
      if (viewModel.get('showOrientedCode') && !viewModel.get('orient')) {
        Ext.Msg.alert('Error', 'Please select a channel orientation', Ext.emptyFn);
        return false;
      }
      let items = this.getView().items;
      for (let i = 0; i < items.getCount(); i++) {
        let item = items.getAt(i);
        if (item.isHidden && item.isHidden()) {
          continue;
        }
        if (item.validate && !item.validate()) {
          return false;
        }
      }
      return true;
    },
    initComponent: function () {
      let viewModel = this.getViewModel();
      let stepsData = viewModel.get('stepsStoredData') || {};
      // Keep a prior Orientation answer if this card is re-entered; wiping it
      // made the question appear twice and failed validation on Next.
      let preservedOrientation = viewModel.get('orientationApplies');
      if (preservedOrientation !== true && preservedOrientation !== false &&
          (stepsData.orientationApplies === true || stepsData.orientationApplies === false)) {
        preservedOrientation = stepsData.orientationApplies;
      }
      let preservedCode = viewModel.get('sohChannelCode') || stepsData.sohChannelCode || null;
      let preservedPrefix = viewModel.get('codePrefix') || stepsData.codePrefix || null;
      let preservedOrient = viewModel.get('orient') || stepsData.orient || null;

      viewModel.set('codePrefix', preservedPrefix);
      viewModel.set('orient', preservedOrient);
      viewModel.set('sohMode', false);
      viewModel.set('integratedMode', false);
      viewModel.set('orientationApplies', preservedOrientation);
      viewModel.set('sohChannelCode', preservedCode);
      viewModel.set('sohSuggestedPrefix', null);
      viewModel.set('sohSuggestedCode', null);
      viewModel.set('scalarChannel', false);
      viewModel.set('sampleRateKnown', true);
      viewModel.set('resolvedSampleRate', null);
      this.syncOrientationButtons();
      this.syncOrientButtons();

      let knownRate = stepsData.sampleRate || stepsData.sohSampleRate;
      if (this.rateIsKnown(knownRate)) {
        viewModel.set('resolvedSampleRate', knownRate);
        viewModel.set('sampleRateKnown', true);
      } else if (stepsData.selectedLibrary === 'none') {
        viewModel.set('sampleRateKnown', false);
        this.refreshWizardNavigation();
        return;
      }

      let responseType = stepsData.nrlResponseType;
      if (responseType === 'soh') {
        viewModel.set('sohMode', true);
        this.loadSohSuggestion();
        this.refreshWizardNavigation();
        return;
      }
      if (responseType === 'integrated') {
        viewModel.set('integratedMode', true);
      }
      this.loadChannelPrefix();
      this.refreshWizardNavigation();
    },
    rateIsKnown: function (value) {
      if (value === null || value === undefined || value === '' || value === '*') {
        return false;
      }
      return /[0-9]/.test(String(value));
    },
    onAskedSampleRateBlur: function (field) {
      let value = field.getValue();
      if (!this.rateIsKnown(value)) {
        return;
      }
      let viewModel = this.getViewModel();
      viewModel.set('resolvedSampleRate', value);
      let stepsData = viewModel.get('stepsStoredData');
      stepsData.sampleRate = value;
      stepsData.sohSampleRate = value;
      if (viewModel.get('sohMode')) {
        this.loadSohSuggestion();
      } else if (stepsData.selectedLibrary !== 'none') {
        this.loadChannelPrefix();
      }
    },
    applyResolvedRate: function (suggestion) {
      let viewModel = this.getViewModel();
      if (suggestion && this.rateIsKnown(suggestion.sampleRate)) {
        viewModel.set('sampleRateKnown', true);
        if (!this.rateIsKnown(viewModel.get('resolvedSampleRate'))) {
          viewModel.set('resolvedSampleRate', suggestion.sampleRate);
        }
        return;
      }
      if (!this.rateIsKnown(viewModel.get('resolvedSampleRate'))) {
        viewModel.set('sampleRateKnown', false);
      }
    },
    loadChannelPrefix: function () {
      let stepsData = this.getViewModel().get('stepsStoredData');
      Ext.Ajax.request({
        scope: this,
        jsonData: {
          libraryType: stepsData.selectedLibrary,
          nrlResponseType: stepsData.nrlResponseType,
          sensorType: stepsData.sensorType || null,
          angularPeriod: stepsData.angularPeriod || null,
          sampleRate: stepsData.sampleRate || null,
          inputUnits: stepsData.inputUnits || null,
          instconfig: stepsData.instconfig || null,
          description: stepsData.configDescription || '',
          sensorKeys: stepsData.sensorKeys || [],
          dataloggerKeys: stepsData.dataloggerKeys || []
        },
        url: '/api/wizard/guess/prefix/',
        method: 'POST',
        success: function (response) {
          let suggestion = Ext.decode(response.responseText, true) || {};
          let viewModel = this.getViewModel();
          let stepsData = viewModel.get('stepsStoredData');
          this.applyResolvedRate(suggestion);
          if (stepsData.nrlResponseType === 'integrated') {
            // Ask whether orientation applies. A "no" answer uses the
            // SEED name derived from the response input units.
            viewModel.set('sohSuggestedPrefix', suggestion.prefix || '');
            viewModel.set('sohSuggestedCode', suggestion.code || suggestion.prefix || '');
            this.applySohSuggestion();
          } else if (suggestion.orientationApplies === false) {
            viewModel.set('scalarChannel', true);
            if (!viewModel.get('sohChannelCode')) {
              viewModel.set('sohChannelCode', suggestion.code || suggestion.prefix || '');
            }
          } else if (suggestion.prefix && !viewModel.get('codePrefix')) {
            viewModel.set('codePrefix', suggestion.prefix);
          }
          this.refreshWizardNavigation();
        },
        failure: function () {
          Ext.Msg.alert(
            'Channel code',
            'The suggested SEED channel code could not be loaded. You can type the code.'
          );
        }
      });
    },
    loadSohSuggestion: function () {
      let stepsData = this.getViewModel().get('stepsStoredData');
      let payload = {
        channelDescription: stepsData.sohChannelDescription || null,
        sampleRate: stepsData.sohSampleRate || null,
        libraryType: stepsData.selectedLibrary,
        sensorKeys: stepsData.sensorKeys || []
      };
      Ext.Ajax.request({
        scope: this,
        jsonData: payload,
        url: '/api/wizard/guess/soh-code/',
        method: 'POST',
        success: function (response) {
          let suggestion = Ext.decode(response.responseText, true) || {};
          let viewModel = this.getViewModel();
          this.applyResolvedRate(suggestion);
          viewModel.set('sohSuggestedPrefix', suggestion.prefix || '');
          viewModel.set('sohSuggestedCode', suggestion.code || '');
          this.applySohSuggestion();
          this.refreshWizardNavigation();
        },
        failure: function () {
          Ext.Msg.alert(
            'Channel code',
            'The suggested SEED channel code could not be loaded. You can type the code.'
          );
        }
      });
    },
    applySohSuggestion: function () {
      let viewModel = this.getViewModel();
      if (viewModel.get('orientationApplies') === true && !viewModel.get('codePrefix')) {
        viewModel.set('codePrefix', viewModel.get('sohSuggestedPrefix') || '');
      }
      if (viewModel.get('orientationApplies') === false && !viewModel.get('sohChannelCode')) {
        viewModel.set('sohChannelCode', viewModel.get('sohSuggestedCode') || '');
      }
    },
    onOrientationChoice: function (button) {
      let answer = button.choiceValue;
      let viewModel = this.getViewModel();
      if (answer !== 'yes' && answer !== 'no') {
        viewModel.set('orientationApplies', null);
        this.syncOrientationButtons();
        this.refreshWizardNavigation();
        return;
      }
      viewModel.set('orientationApplies', answer === 'yes');
      viewModel.get('stepsStoredData').orientationApplies = answer === 'yes';
      this.syncOrientationButtons();
      this.applySohSuggestion();
      this.refreshWizardNavigation();
    },
    onOrientChoice: function (button) {
      this.getViewModel().set('orient', button.choiceValue);
      this.syncOrientButtons();
    },
    syncOrientationButtons: function () {
      let value = this.getViewModel().get('orientationApplies');
      let selected = value === true ? 'yes' : (value === false ? 'no' : null);
      Ext.Array.each(this.getView().query('button[choiceGroup=orientationApplies]'), function (btn) {
        btn.toggle(btn.choiceValue === selected, true);
      });
    },
    syncOrientButtons: function () {
      let selected = this.getViewModel().get('orient');
      Ext.Array.each(this.getView().query('button[choiceGroup=orient]'), function (btn) {
        btn.toggle(btn.choiceValue === selected, true);
      });
    },
    refreshWizardNavigation: function () {
      let wizard = this.getView().up('wizard-per-sample-rate-channel');
      if (wizard) {
        wizard.getController().updateNavigationButtonState();
      }
    },
    storeStepData: function () {
      let viewModel = this.getViewModel();
      let orient = viewModel.get('orient');
      let codePrefix = viewModel.get('codePrefix');
      let channelInfo = this.getViewModel().get('channelInfo');
      let stepsData = viewModel.get('stepsStoredData');
      stepsData.orientationApplies = viewModel.get('orientationApplies');
      stepsData.sohChannelCode = viewModel.get('sohChannelCode');
      stepsData.codePrefix = codePrefix;
      stepsData.orient = orient;
      if (this.rateIsKnown(viewModel.get('resolvedSampleRate'))) {
        channelInfo.set('sampleRate', viewModel.get('resolvedSampleRate'));
      }

      if (viewModel.get('scalarChannel') || (viewModel.get('asksOrientation') && viewModel.get('orientationApplies') === false)) {
        channelInfo.set('code1', viewModel.get('sohChannelCode') || '');
        channelInfo.set('code2', '');
        channelInfo.set('code3', '');
        channelInfo.set('omitDipAzimuth', true);
        return;
      }
      channelInfo.set('omitDipAzimuth', false);

      if (orient === yasmine.ChannelOrient.ZNE) {
        channelInfo.set('code1', codePrefix + 'Z')
        channelInfo.set('code2', codePrefix + 'N')
        channelInfo.set('code3', codePrefix + 'E')
        channelInfo.set('dip1', -90)
        channelInfo.set('dip2', 0)
        channelInfo.set('dip3', 0)
        channelInfo.set('azimuth1', 0)
        channelInfo.set('azimuth2', 0)
        channelInfo.set('azimuth3', 90)
      } else if (orient === yasmine.ChannelOrient.Z12) {
        channelInfo.set('code1', codePrefix + 'Z')
        channelInfo.set('code2', codePrefix + '1')
        channelInfo.set('code3', codePrefix + '2')
        channelInfo.set('dip1', 0)
        channelInfo.set('dip2', 0)
        channelInfo.set('dip3', 0)
        channelInfo.set('azimuth1', 0)
        channelInfo.set('azimuth2', 0)
        channelInfo.set('azimuth3', 0)
      } else if (orient === yasmine.ChannelOrient.Z) {
        channelInfo.set('code1', codePrefix + 'Z')
        channelInfo.set('code2', '')
        channelInfo.set('code3', '')
        channelInfo.set('dip1', -90)
        channelInfo.set('dip2', 0)
        channelInfo.set('dip3', 0)
        channelInfo.set('azimuth1', 0)
        channelInfo.set('azimuth2', 0)
        channelInfo.set('azimuth3', 0)
      }
    }
  },
  layout: {
    type: 'vbox',
    align: 'stretch',
    pack: 'start'
  },
  maxWidth: 420,
  minWidth: 0,
  defaults: {
    labelWidth: 150,
  },
  items: [
    {
      xtype: 'numberfield',
      reference: 'askedSampleRate',
      fieldLabel: 'Sample Rate (Hz)',
      minValue: 0,
      allowDecimals: true,
      decimalPrecision: 6,
      allowBlank: false,
      bind: {
        hidden: '{sampleRateKnown}'
      },
      listeners: {
        blur: 'onAskedSampleRateBlur'
      }
    },
    {
      xtype: 'fieldcontainer',
      reference: 'orientationApplies',
      fieldLabel: 'Orientation applies',
      layout: {
        type: 'vbox',
        align: 'stretch'
      },
      bind: {
        hidden: '{!showSohQuestion}'
      },
      items: [
        {
          xtype: 'container',
          cls: 'yasmine-wizard-choice-list yasmine-wizard-choice-list-compact',
          layout: {
            type: 'hbox',
            align: 'stretch'
          },
          defaults: {
            xtype: 'button',
            enableToggle: true,
            allowDepress: false,
            flex: 1,
            margin: '0 8 0 0',
            cls: 'yasmine-wizard-choice-btn',
            choiceGroup: 'orientationApplies',
            handler: 'onOrientationChoice'
          },
          items: [
            {text: 'Yes', choiceValue: 'yes'},
            {text: 'No', choiceValue: 'no', margin: 0}
          ]
        }
      ]
    },
    {
      xtype: 'textfield',
      fieldLabel: 'Channel code',
      bind: {
        value: '{sohChannelCode}',
        hidden: '{!showSohName}'
      },
      maxLength: 3,
      enforceMaxLength: true,
      allowBlank: false
    },
    {
      xtype: 'textfield',
      fieldLabel: 'Channel Prefix',
      reference: 'codePrefix',
      bind: {
        value: '{codePrefix}',
        hidden: '{!showOrientedCode}'
      },
      maxLength: 2,
      enforceMaxLength: true,
      allowBlank: false
    },
    {
      xtype: 'fieldcontainer',
      fieldLabel: 'Channel Orientation',
      layout: {
        type: 'vbox',
        align: 'stretch'
      },
      bind: {
        hidden: '{!showOrientedCode}'
      },
      items: [
        {
          xtype: 'container',
          cls: 'yasmine-wizard-choice-list',
          layout: {
            type: 'vbox',
            align: 'stretch'
          },
          defaults: {
            xtype: 'button',
            enableToggle: true,
            allowDepress: false,
            textAlign: 'left',
            margin: '0 0 8 0',
            cls: 'yasmine-wizard-choice-btn',
            choiceGroup: 'orient',
            handler: 'onOrientChoice'
          },
          items: [
            {text: 'ZNE (3 channels)', choiceValue: yasmine.ChannelOrient.ZNE},
            {text: 'Z12 (3 channels)', choiceValue: yasmine.ChannelOrient.Z12},
            {text: 'Z (1 channel)', choiceValue: yasmine.ChannelOrient.Z, margin: 0}
          ]
        }
      ]
    }
  ]
});

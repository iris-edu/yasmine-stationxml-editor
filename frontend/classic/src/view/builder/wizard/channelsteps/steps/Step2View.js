/* ****************************************************************************
* 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
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


Ext.define('yasmine.view.xml.builder.wizard.channelsteps.steps.Step2View', {
  extend: 'Ext.panel.Panel',
  xtype: 'channel-step-2',
  controller: {
    selectedValue: null,
    isValid: function () {
      if (!this.getSelectedValue()) {
        Ext.Msg.alert('Error', 'Please make a choice', Ext.emptyFn);
        return false;
      }
      return true;
    },
    storeStepData: function () {
      let viewModel = this.getViewModel();
      let library = this.getSelectedValue();
      viewModel.get('stepsStoredData').selectedLibrary = library;
      viewModel.set('selectedLibrary', library);
      viewModel.get('channelInfo').set('libraryType', library);
      if (library !== 'nrl' && library !== 'nrlv2_online') {
        viewModel.get('stepsStoredData').nrlResponseType = null;
        viewModel.set('nrlResponseType', null);
        viewModel.get('channelInfo').set('nrlResponseType', null);
      }
    },
    getSelectedValue: function () {
      return this.selectedValue;
    },
    selectLibrary: function (value) {
      this.selectedValue = value;
      this.getViewModel().set('selectedLibrary', value);
      this.syncChoiceButtons();
      let wizard = this.getView().up('wizard-per-sample-rate-channel');
      if (wizard) {
        wizard.getController().updateNavigationButtonState();
      }
    },
    syncChoiceButtons: function () {
      let selected = this.selectedValue;
      Ext.Array.each(this.getView().query('button[choiceValue]'), function (btn) {
        btn.toggle(btn.choiceValue === selected, true);
      });
    },
    onLibraryChoice: function (button) {
      if (button.isDisabled()) {
        return;
      }
      this.selectLibrary(button.choiceValue);
    }
  },
  layout: {
    type: 'vbox',
    align: 'stretch'
  },
  items: [
    {
      xtype: 'component',
      html: '<b>Select a library to build a response.</b>',
      margin: '0 0 12 0'
    },
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
        handler: 'onLibraryChoice'
      },
      items: [
        {
          text: 'NRL Offline (downloaded archive)',
          choiceValue: 'nrl'
        },
        {
          text: 'AROL',
          choiceValue: 'arol'
        },
        {
          text: 'NRL Online',
          choiceValue: 'nrlv2_online',
          bind: {
            disabled: '{!nrlv2OnlineEnabled}',
            tooltip: '{nrlv2OnlineTooltip}'
          }
        },
        {
          text: 'I don\'t need a response',
          choiceValue: 'none'
        }
      ]
    }
  ]
});

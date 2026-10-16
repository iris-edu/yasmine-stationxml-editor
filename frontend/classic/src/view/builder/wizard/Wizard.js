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
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.wizard.WizardView', {
  extend: 'Ext.window.Window',
  xtype: 'wizard-create',
  requires: [
    'yasmine.view.xml.builder.wizard.WizardCreateController',
    'yasmine.view.xml.builder.wizard.WizardCreateModel',
    'yasmine.view.xml.builder.wizard.networksteps.WizardCreateNetworkView',
    'yasmine.view.xml.builder.wizard.stationsteps.WizardCreateStationView',
    'yasmine.view.xml.builder.wizard.channelsteps.WizardCreateChannelView',
    'yasmine.view.xml.builder.wizard.finalsteps.WizardFinalStepView'
  ],
  controller: 'wizard-create',
  viewModel: 'wizard-create',
  cls: 'yasmine-window yasmine-wizard-window',
  modal: true,
  frame: false,
  constrain: true,
  closable: false,
  bodyPadding: 5,
  bodyBorder: true,
  layout: 'card',
  minWidth: 280,
  minHeight: 200,
  listeners: {
    show: function () {
      if (!this._initialSizeApplied) {
        yasmine.utils.ResponsiveUtil.fitWindow(this, {
          minWidth: 800,
          minHeight: 600,
          width: 1000,
          height: 700
        });
        this._initialSizeApplied = true;
      }
    },
    resize: function () {
      yasmine.utils.ResponsiveUtil.clampWindow(this);
    }
  },
  bind: {
    activeItem: '{currentIndex}',
    title: '{currentTitle}'
  },
  items: [
    {xtype: 'wizard-create-network'},
    {xtype: 'wizard-create-station'},
    {xtype: 'wizard-create-channel'},
    {xtype: 'wizard-final-step'}
  ],
  buttonAlign: 'right',
  buttons: [
    {
      xtype: 'container',
      reference: 'wizard-action-buttons-container',
      cls: 'yasmine-wrap-toolbar yasmine-action-buttons',
      minWidth: 0,
      defaults: {
        margin: '0 5 0 0'
      },
      items: []
    },
    '->',
    {
      text: '&laquo; Previous',
      iconCls: 'x-fa fa-arrow-left',
      hidden: true,
      bind: {
        hidden: '{!hasPrevious}'
      },
      handler: 'onPrevious'
    },
    {
      text: 'Next &raquo;',
      iconCls: 'x-fa fa-arrow-right',
      iconAlign: 'right',
      cls: 'yasmine-primary-action',
      bind: {
        hidden: '{!hasNext}'
      },
      handler: 'onNext'
    },
    {
      text: 'Complete Wizard',
      iconCls: 'x-fa fa-check',
      cls: 'yasmine-primary-action',
      bind: {
        hidden: '{hasNext}'
      },
      hidden: true,
      handler: 'onSave'
    }
  ],
  tools: [
    {
      type: 'help',
      tooltip: 'Help for the field you are filling',
      handler: 'onHelpClick'
    },
    {
      type: 'maximize',
      handler: 'onMaximizeClick'
    },
    {
      type: 'close',
      handler: 'onCancelClick'
    }
  ]
});

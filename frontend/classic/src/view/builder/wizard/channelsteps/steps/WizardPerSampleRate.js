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
* 2019/10/07 : version 2.0.0 initial commit
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.wizard.channelsteps.steps.WizardPerSampleRate', {
  extend: 'Ext.panel.Panel',
  xtype: 'wizard-per-sample-rate-channel',
  requires: [
    'yasmine.view.xml.builder.wizard.channelsteps.steps.WizardCreateChannelController',
    'yasmine.view.xml.builder.wizard.channelsteps.steps.WizardCreateChannelModel',
    'yasmine.view.xml.builder.wizard.channelsteps.steps.Step1View',
    'yasmine.view.xml.builder.wizard.channelsteps.steps.Step2View',
    'yasmine.view.xml.builder.wizard.channelsteps.steps.Step3View',
    'yasmine.view.xml.builder.wizard.channelsteps.steps.Step4View',
    'yasmine.view.xml.builder.wizard.channelsteps.steps.Step5View'
  ],
  controller: 'wizard-create-channel-item',
  viewModel: 'wizard-create-channel-item',
  layout: 'card',
  bind: {
    activeItem: '{activeIndex}',
    title: '{completionStatusLabel} Sample Rate #{sampleRateNumber}'
  },
  items: [
    {
      layout: {type: 'vbox', align: 'center'},
      items: [
        {
          flex: 1,
          bind: {
            html: '<div style="width: 100%; text-align: center; font-size: 14px; font-weight: bold; padding-top: 15px;">Sample Rate #{sampleRateNumber} / Step 1 of 5</div>'
          }
        },
        {xtype: 'channel-step-1', reference: 'channel-step-1'},
        {flex: 1}
      ]
    },
    {
      layout: {type: 'vbox', align: 'center'},
      items: [
        {
          flex: 1,
          bind: {
            html: '<div style="width: 100%; text-align: center; font-size: 14px; font-weight: bold; padding-top: 15px;">Sample Rate #{sampleRateNumber} / Step 2 of 5</div>'
          }
        },
        {xtype: 'channel-step-2', reference: 'channel-step-2'},
        {flex: 1}
      ]
    },
    {
      layout: {type: 'vbox', align: 'stretch', pack: ''},
      items: [
        {
          height: 50,
          bind: {
            html: '<div style="width: 100%; text-align: center; font-size: 14px; font-weight: bold; padding-top: 15px;">Sample Rate #{sampleRateNumber} / Step 3 of 5</div>'
          }
        },
        {xtype: 'channel-step-3', reference: 'channel-step-3', flex: 1, layout: 'fit'},
      ]
    },
    {
      layout: {type: 'vbox', align: 'center'},
      items: [
        {
          flex: 1,
          bind: {
            html: '<div style="width: 100%; text-align: center; font-size: 14px; font-weight: bold; padding-top: 15px;">Sample Rate #{sampleRateNumber} / Step 4 of 5</div>'
          }
        },
        {xtype: 'channel-step-4', reference: 'channel-step-4'},
        {flex: 1}
      ]
    },
    {
      layout: {type: 'vbox', align: 'center'},
      items: [
        {
          flex: 1,
          bind: {
            html: '<div style="width: 100%; text-align: center; font-size: 14px; font-weight: bold; padding-top: 15px;">Sample Rate #{sampleRateNumber} / Step 5 of 5</div>'
          }
        },
        {xtype: 'channel-step-5', reference: 'channel-step-5'},
        {flex: 1}
      ]
    },
  ],
});

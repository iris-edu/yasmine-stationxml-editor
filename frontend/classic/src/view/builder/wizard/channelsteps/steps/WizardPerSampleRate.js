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
* 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
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
    'yasmine.view.xml.builder.wizard.channelsteps.steps.StepNrlTypeView',
    'yasmine.view.xml.builder.wizard.channelsteps.steps.Step3View',
    'yasmine.view.xml.builder.wizard.channelsteps.steps.Step4View',
    'yasmine.view.xml.builder.wizard.channelsteps.steps.Step5View'
  ],
  controller: 'wizard-create-channel-item',
  viewModel: 'wizard-create-channel-item',
  layout: {
    type: 'card',
    deferredRender: true
  },
  bind: {
    activeItem: '{activeIndex}',
    title: '{panelTitle}'
  },
  // Centered vbox + flex spacers never finishes on a narrow window: Ext's box
  // layout leaves the inner element at height 0 and clips the form.
  defaults: {
    border: false,
    bodyBorder: false,
    scrollable: true,
    layout: 'center'
  },
  items: [
    {
      itemId: 'wizard-card-1',
      items: [
        {
          xtype: 'container',
          width: '100%',
          maxWidth: 420,
          minWidth: 0,
          layout: {type: 'vbox', align: 'stretch'},
          items: [
            {
              xtype: 'component',
              margin: '12 8 8 8',
              cls: 'yasmine-wizard-step-heading',
              bind: {
                html: '<div class="yasmine-wizard-step-heading-text">{locationStepHeading}</div>'
              }
            },
            {xtype: 'channel-step-1', reference: 'channel-step-1'}
          ]
        }
      ]
    },
    {
      itemId: 'wizard-card-2',
      items: [
        {
          xtype: 'container',
          width: '100%',
          maxWidth: 420,
          minWidth: 0,
          layout: {type: 'vbox', align: 'stretch'},
          items: [
            {
              xtype: 'component',
              margin: '12 8 8 8',
              cls: 'yasmine-wizard-step-heading',
              bind: {
                html: '<div class="yasmine-wizard-step-heading-text">{libraryStepHeading}</div>'
              }
            },
            {xtype: 'channel-step-2', reference: 'channel-step-2'}
          ]
        }
      ]
    },
    {
      itemId: 'wizard-card-type',
      items: [
        {
          xtype: 'container',
          width: '100%',
          maxWidth: 420,
          minWidth: 0,
          layout: {type: 'vbox', align: 'stretch'},
          items: [
            {
              xtype: 'component',
              margin: '12 8 8 8',
              cls: 'yasmine-wizard-step-heading',
              bind: {
                html: '<div class="yasmine-wizard-step-heading-text">{typeStepHeading}</div>'
              }
            },
            {xtype: 'channel-nrl-response-type', reference: 'channel-nrl-response-type'}
          ]
        }
      ]
    },
    {
      itemId: 'wizard-card-3',
      scrollable: false,
      layout: 'fit',
      items: [
        {
          xtype: 'panel',
          border: false,
          layout: 'fit',
          dockedItems: [
            {
              xtype: 'component',
              dock: 'top',
              margin: '12 8 4 8',
              cls: 'yasmine-wizard-step-heading',
              bind: {
                html: '<div class="yasmine-wizard-step-heading-text">{selectorStepHeading}</div>'
              }
            }
          ],
          items: [
            {xtype: 'channel-step-3', reference: 'channel-step-3', layout: 'fit', minHeight: 0}
          ]
        }
      ]
    },
    {
      itemId: 'wizard-card-4',
      items: [
        {
          xtype: 'container',
          width: '100%',
          maxWidth: 420,
          minWidth: 0,
          layout: {type: 'vbox', align: 'stretch'},
          items: [
            {
              xtype: 'component',
              margin: '12 8 8 8',
              cls: 'yasmine-wizard-step-heading',
              bind: {
                html: '<div class="yasmine-wizard-step-heading-text">{codeStepHeading}</div>'
              }
            },
            {xtype: 'channel-step-4', reference: 'channel-step-4'}
          ]
        }
      ]
    },
    {
      itemId: 'wizard-card-5',
      items: [
        {
          xtype: 'container',
          width: '100%',
          maxWidth: 420,
          minWidth: 0,
          layout: {type: 'vbox', align: 'stretch'},
          items: [
            {
              xtype: 'component',
              margin: '12 8 8 8',
              cls: 'yasmine-wizard-step-heading',
              bind: {
                html: '<div class="yasmine-wizard-step-heading-text">{detailStepHeading}</div>'
              }
            },
            {xtype: 'channel-step-5', reference: 'channel-step-5'}
          ]
        }
      ]
    }
  ]
});

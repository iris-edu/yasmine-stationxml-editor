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
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.nrl.NrlResponseSelector', {
  extend: 'Ext.tab.Panel',
  xtype: 'nrl-response-selector',
  requires: [
    'Ext.toolbar.Breadcrumb',
    'yasmine.view.xml.builder.parameter.items.channelresponse.nrlselector.NrlResponseSelectorController',
    'yasmine.view.xml.builder.parameter.items.channelresponse.nrlselector.NrlResponseSelectorModel',
    'yasmine.view.xml.builder.parameter.items.channelresponse.preview.ResponsePreview'
  ],
  controller: 'nrl-response-selector',
  viewModel: 'nrl-response-selector',
  reference: 'nrl-response-selector',
  style: 'border: solid #d0d0d0 1px;',
  items: [
    // Datalogger
    {
      bind: {
        title: '{dataloggerStatus} Datalogger'
      },
      flex: 1,
      layout: {
        type: 'vbox',
        align: 'stretch'
      },
      bodyPadding: 5,
      items: [
        {
          xtype: 'breadcrumb',
          showMenuIcons: true,
          showIcons: true,
          scrollable: true,
          height: 200,
          layout: 'vbox',
          useSplitButtons: false,
          componentCls: 'equipment',
          displayField: 'title',
          reference: 'dataloggerCmp',
          bind: {
            store: '{dataloggerStore}',
            selection: '{dataloggerSelection}'
          },
          defaults: {
            listeners: {
              click: 'onDataloggerClick'
            }
          },
          listeners: {
            change: 'onDataloggerSelectionChange'
          }
        },
        {
          xtype: 'textareafield',
          flex: 1,
          readOnly: true,
          scrollable: true,
          padding: '5 0 0 0',
          fieldStyle: {
            'fontFamily': 'Consolas,Monaco,Lucida Console,Liberation Mono,DejaVu Sans Mono,Bitstream Vera Sans Mono,Courier New, monospace;',
            'fontSize': '11px',
            'white-space': 'pre'
          },
          bind: {
            value: '{dataloggerPreview}'
          }
        }
      ]
    },
    // Sensor
    {
      bind: {
        title: '{sensorStatus} Sensor'
      },
      flex: 1,
      layout: {
        type: 'vbox',
        align: 'stretch'
      },
      bodyPadding: 5,
      items: [
        {
          xtype: 'breadcrumb',
          showMenuIcons: true,
          showIcons: true,
          scrollable: true,
          height: 200,
          layout: 'vbox',
          useSplitButtons: false,
          componentCls: 'equipment',
          displayField: 'title',
          reference: 'sensorCmp',
          bind: {
            store: '{sensorStore}',
            selection: '{sensorSelection}'
          },
          defaults: {
            listeners: {
              click: 'onSensorClick'
            }
          },
          listeners: {
            change: 'onSensorSelectionChange'
          }
        },
        {
          xtype: 'textareafield',
          flex: 1,
          readOnly: true,
          scrollable: true,
          padding: '5 0 0 0',
          fieldStyle: {
            'fontFamily': 'Consolas,Monaco,Lucida Console,Liberation Mono,DejaVu Sans Mono,Bitstream Vera Sans Mono,Courier New, monospace;',
            'fontSize': '11px',
            'white-space': 'pre'
          },
          bind: {
            value: '{sensorPreview}'
          }
        }
      ]
    },
    // Response
    {
      bind: {
        title: '{responseStatus} Response',
        disabled: '{!channelResponseText}'
      },
      disabled: true,
      flex: 1,
      layout: 'fit',
      bodyPadding: 5,
      items: [
        {
          xtype: 'response-preview'
        }
      ]
    }
  ]
});

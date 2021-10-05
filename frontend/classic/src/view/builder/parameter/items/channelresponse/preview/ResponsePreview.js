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


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.preview.ResponsePreview', {
  extend: 'Ext.container.Container',
  xtype: 'response-preview',
  requires: [
    'yasmine.view.xml.builder.parameter.items.channelresponse.preview.ResponseChart'
  ],
  viewModel: {
    data: {
      isChartMode: true
    }
  },
  layout: {
    type: 'vbox',
    pack: 'start',
    align: 'stretch'
  },
  items: [
    {
      xtype: 'container',
      items: {
        xtype: 'segmentedbutton',
        defaults: {
          width: 100
        },
        items: [
          {
            text: 'Response Plot',
            pressed: true,
            iconCls: 'fa fa-area-chart',
            listeners: {
              click: function () {
                this.lookupViewModel().set('isChartMode', true);
              }
            }
          },
          {
            text: 'Channel Response',
            iconCls: 'fa fa-file-text',
            listeners: {
              click: function () {
                this.lookupViewModel().set('isChartMode', false);
              }
            }
          }
        ]
      }
    },
    {
      xtype: 'container',
      flex: 1,
      layout: 'fit',
      hidden: true,
      padding: '5 0 0 0',
      bind: {
        hidden: '{isChartMode}',
      },
      items: {
        xtype: 'textareafield',
        readOnly: true,
        fieldStyle: {
          'fontFamily': 'Consolas,Monaco,Lucida Console,Liberation Mono,DejaVu Sans Mono,Bitstream Vera Sans Mono,Courier New, monospace;',
          'fontSize': '11px',
          'white-space': 'pre'
        },
        bind: {
          scrollable: true,
          value: '{channelResponseText}'
        }
      }
    },
    {
      xtype: 'response-chart',
      flex: 1,
      margin: '5 0 0 0',
      hidden: false,
      bind: {
        hidden: '{!isChartMode}',
      }
    }
  ]
});

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


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.preview.ResponseChart', {
  extend: 'Ext.container.Container',
  xtype: 'response-chart',
  style: {
    'border-width': 'thin',
    'border-style': 'solid',
    'border-color': '#d0d0d0'
  },
  viewModel: {
    data: {
      showChartControls: true,
      showDownloadButtons: true
    }
  },
  layout: {
    type: 'vbox',
    align: 'stretch'
  },
  items: [
    {
      padding: '0 0 0 5',
      layout: {
        type: 'hbox',
        pack: 'center',
        padding: '5 0 0 0'
      },
      height: 38,
      hidden: true,
      bind: {
        hidden: '{!channelResponseImageUrl || !showChartControls}'
      },
      items: [
        {
          xtype: 'numberfield',
          fieldLabel: 'Min <i class="fa fa-question-circle" data-qtip="Min Frequency"></i>',
          labelWidth: 50,
          width: 150,
          allowDecimals: true,
          decimalPrecision: 5,
          minValue: 0,
          margin: '0 10 0 0',
          bind: {
            value: '{minFrequency}'
          }
        },
        {
          xtype: 'numberfield',
          fieldLabel: 'Max <i class="fa fa-question-circle" data-qtip="Max Frequency"></i>',
          labelWidth: 50,
          width: 150,
          allowDecimals: true,
          decimalPrecision: 5,
          minValue: 0,
          margin: '0 10 0 0',
          bind: {
            value: '{maxFrequency}'
          }
        },
        {
          xtype: 'button',
          iconCls: 'fa fa-refresh',
          tooltip: 'Rebuild Plot',
          handler: 'loadChannelResponsePlot'
        }
      ]
    },
    {
      layout: 'hbox',
      items: [
        {
          xtype: 'button',
          hidden: true,
          margin: '0 0 0 10',
          bind: {
            hidden: '{!channelResponseImageUrl|| !showDownloadButtons}'
          },
          iconCls: 'fa fa-area-chart',
          tooltip: 'Download Plot',
          handler: 'downloadChannelResponsePlot'
        },
        {
          xtype: 'button',
          hidden: true,
          margin: '0 0 0 10',
          bind: {
            hidden: '{!channelResponseImageUrl || !showDownloadButtons}'
          },
          iconCls: 'fa fa-table',
          tooltip: 'Download CSV',
          handler: 'downloadChannelResponseCsv'
        },
      ]
    },
    {
      xtype: 'image',
      flex: 1,
      style: {
        'object-fit': 'scale-down'
      },
      bind: {
        src: '{channelResponseImageUrl}'
      }
    },
  ]

});

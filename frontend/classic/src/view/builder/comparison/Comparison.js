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


Ext.define('yasmine.view.xml.builder.comparison.Comparison', {
  extend: 'Ext.panel.Panel',
  xtype: 'xml-comparison',
  requires: [
    'yasmine.view.xml.builder.comparison.ComparisonController',
    'yasmine.view.xml.builder.comparison.ComparisonModel',
    'yasmine.view.xml.builder.parameter.items.channelresponse.preview.ResponseChart'
  ],
  viewModel: 'comparison',
  controller: 'comparison',
  title: 'Compare',
  layout: {
    type: 'vbox',
    align: 'stretch'
  },
  bodyBorder: true,
  tbar: {
    style: 'background-color: #ecebeb',
    items: [
      {
        xtype: 'numberfield',
        fieldLabel: 'Min Frequency',
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
        fieldLabel: 'Max Frequency',
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
        tooltip: 'Rebuild Plots',
        text: 'Rebuild Plots',
        handler: 'rebuildPlots'
      }
    ]
  },
  items: [
    {
      layout: {
        type: 'hbox',
        align: 'stretch'
      },
      flex: 1,
      items: [
        {
          tbar: {
            height: 44,
            items: [
              {
                xtype: 'panel',
                bind: {
                  html: 'XML: <b>{xml.name}</b>'
                }
              },
              '->',
              {
                xtype: 'panel',
                bind: {
                  html: 'Channel: <b>{xml1ChannelTitle}</b>'
                }
              }
            ]
          },
          style: 'border-right: solid #d0d0d0 1px;',
          flex: 1,
          layout: 'fit',
          items: [
            {
              style: 'border-top: solid #d0d0d0 1px;',
              hidden: true,
              bind: {
                hidden: '{!xml1ChartMessage}',
                html: '<div style="height: 100%; display: flex; justify-content: center; align-items: center; font-weight: 700; font-size: 16px">{xml1ChartMessage}</div>'
              }
            },
            {
              style: 'border-top: solid #d0d0d0 1px;',
              xtype: 'response-chart',
              reference: 'xml1Chart',
              hidden: true,
              bind: {
                hidden: '{xml1ChartMessage}'
              },
              viewModel: {
                data: {
                  showChartControls: false,
                  showDownloadButtons: false,
                  channelResponseImageUrl: null
                }
              }
            }
          ]
        },
        {
          tbar: [
            {
              xtype: 'combobox',
              emptyText: 'Select XML',
              displayField: 'name',
              queryMode: 'local',
              bind: {
                store: '{xmlStore}'
              },
              listeners: {
                select: 'onXml2Select'
              },
              fieldStyle: 'font-weight: 700'
            },
            '->',
            {
              xtype: 'panel',
              bind: {
                html: 'Channel: <b>{xml2ChannelTitle}</b>'
              }
            }
          ],
          flex: 1,
          layout: 'fit',
          items: [
            {
              style: 'border-top: solid #d0d0d0 1px;',
              hidden: true,
              bind: {
                hidden: '{!xml2ChartMessage}',
                html: '<div style="height: 100%; display: flex; justify-content: center; align-items: center; font-weight: 700; font-size: 16px">{xml2ChartMessage}</div>'
              },
            },
            {
              style: 'border-top: solid #d0d0d0 1px;',
              xtype: 'response-chart',
              reference: 'xml2Chart',
              hidden: true,
              bind: {
                hidden: '{xml2ChartMessage}'
              },
              viewModel: {
                data: {
                  showChartControls: false,
                  showDownloadButtons: false,
                  channelResponseImageUrl: null
                }
              }
            }
          ]
        }
      ]
    },
    {
      style: 'border-top: solid #d0d0d0 1px;',
      layout: 'fit',
      flex: 1,
      items: [
        {
          hidden: true,
          bind: {
            hidden: '{!xml3ChartMessage}',
            html: '<div style="height: 100%; display: flex; justify-content: center; align-items: center; font-weight: 700; font-size: 16px">{xml3ChartMessage}</div>'
          },
        },
        {
          xtype: 'response-chart',
          reference: 'xml3Chart',
          hidden: true,
          bind: {
            hidden: '{xml3ChartMessage}'
          },
          viewModel: {
            data: {
              showChartControls: false,
              showDownloadButtons: false
            }
          }
        }
      ],
    }
  ]
});

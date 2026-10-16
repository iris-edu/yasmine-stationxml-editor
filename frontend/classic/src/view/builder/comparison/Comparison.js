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
* 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.comparison.Comparison', {
  extend: 'Ext.panel.Panel',
  xtype: 'xml-comparison',
  requires: [
    'Ext.plugin.Responsive',
    'yasmine.utils.ResponseRecalculateUtil',
    'yasmine.view.xml.builder.comparison.ComparisonController',
    'yasmine.view.xml.builder.comparison.ComparisonModel',
    'yasmine.view.xml.builder.parameter.items.channelresponse.preview.ResponseChart'
  ],
  viewModel: 'comparison',
  controller: 'comparison',
  title: 'Compare',
  cls: 'xml-comparison',
  scrollable: 'y',
  layout: {
    type: 'vbox',
    align: 'stretch'
  },
  bodyBorder: true,
  tbar: {
    cls: 'yasmine-compare-toolbar',
    layout: {
      type: 'hbox',
      align: 'middle'
    },
    items: [
      {
        xtype: 'numberfield',
        fieldLabel: 'Min',
        labelWidth: 32,
        flex: 1,
        minWidth: 0,
        allowDecimals: true,
        decimalPrecision: 5,
        minValue: 0,
        hideTrigger: true,
        keyNavEnabled: false,
        mouseWheelEnabled: false,
        margin: '0 10 0 0',
        bind: {
          value: '{minFrequency}'
        },
        listeners: {
          change: function (field, newValue) {
            yasmine.utils.ResponseRecalculateUtil.limitMaxForPointBudget(
              field.lookupViewModel(), newValue);
          },
          specialkey: function (field, e) {
            if (e.getKey() === e.ENTER) {
              e.stopEvent();
              var ctrl = field.lookupController();
              if (ctrl && typeof ctrl.rebuildPlots === 'function') {
                ctrl.rebuildPlots();
              }
              return false;
            }
          }
        }
      },
      {
        xtype: 'numberfield',
        fieldLabel: 'Max',
        labelWidth: 32,
        flex: 1,
        minWidth: 0,
        allowDecimals: true,
        decimalPrecision: 5,
        minValue: 0,
        hideTrigger: true,
        keyNavEnabled: false,
        mouseWheelEnabled: false,
        margin: '0 10 0 0',
        bind: {
          value: '{maxFrequency}'
        },
        listeners: {
          specialkey: function (field, e) {
            if (e.getKey() === e.ENTER) {
              e.stopEvent();
              var ctrl = field.lookupController();
              if (ctrl && typeof ctrl.rebuildPlots === 'function') {
                ctrl.rebuildPlots();
              }
              return false;
            }
          }
        }
      },
      {
        xtype: 'button',
        iconCls: 'x-fa fa-refresh',
        tooltip: 'Rebuild Plots',
        text: '',
        handler: 'rebuildPlots'
      }
    ]
  },
  listeners: {
    afterrender: 'syncComparisonSplit'
  },
  items: [
    {
      reference: 'comparisonSplit',
      layout: {
        type: 'hbox',
        align: 'stretch'
      },
      flex: 1,
      minHeight: 220,
      items: [
        {
          tbar: {
            items: [
              {
                xtype: 'component',
                flex: 1,
                minWidth: 0,
                bind: {
                  html: '<div style="padding:2px 0;line-height:1.35">XML: <b>{xml.name}</b><br>Channel: <b>{xml1ChannelTitle}</b></div>'
                }
              }
            ]
          },
          cls: 'yasmine-compare-pane yasmine-compare-pane-primary',
          flex: 1,
          minHeight: 160,
          plugins: 'responsive',
          responsiveConfig: {
            'width < 1280 || height < 500': {
              flex: 1,
              height: null,
              minHeight: 240
            },
            'width >= 1280 && height >= 500': {
              flex: 1,
              height: null,
              minHeight: 160
            }
          },
          layout: 'fit',
          items: [
            {
              xtype: 'response-chart',
              cls: 'comparison-chart yasmine-section-divider',
              reference: 'xml1Chart',
              hidden: true,
              bind: {
                hidden: '{xml1ChartMessage}'
              }
            },
            {
              cls: 'yasmine-section-divider',
              hidden: true,
              bind: {
                hidden: '{!xml1ChartMessage}',
                html: '<div class="yasmine-compare-msg">{xml1ChartMessage}</div>'
              }
            }
          ]
        },
        {
          cls: 'yasmine-compare-pane',
          tbar: {
            layout: {
              type: 'hbox',
              align: 'middle'
            },
            items: [
              {
                xtype: 'combobox',
                emptyText: 'Select XML',
                displayField: 'name',
                queryMode: 'local',
                flex: 1,
                minWidth: 0,
                bind: {
                  store: '{xmlStore}'
                },
                listeners: {
                  select: 'onXml2Select'
                },
                fieldStyle: 'font-weight: 700'
              },
              {
                xtype: 'component',
                margin: '0 0 0 8',
                minWidth: 0,
                bind: {
                  html: 'Ch: <b>{xml2ChannelTitle}</b>'
                }
              }
            ]
          },
          flex: 1,
          minHeight: 160,
          plugins: 'responsive',
          responsiveConfig: {
            'width < 1280 || height < 500': {
              flex: 1,
              height: null,
              minHeight: 240
            },
            'width >= 1280 && height >= 500': {
              flex: 1,
              height: null,
              minHeight: 160
            }
          },
          layout: 'fit',
          items: [
            {
              xtype: 'response-chart',
              cls: 'comparison-chart yasmine-section-divider',
              reference: 'xml2Chart',
              hidden: true,
              bind: {
                hidden: '{xml2ChartMessage}'
              }
            },
            {
              cls: 'yasmine-section-divider',
              hidden: true,
              bind: {
                hidden: '{!xml2ChartMessage}',
                html: '<div class="yasmine-compare-msg">{xml2ChartMessage}</div>'
              }
            }
          ]
        }
      ]
    },
    {
      cls: 'yasmine-section-divider yasmine-compare-result',
      layout: 'fit',
      flex: 1,
      minHeight: 160,
      plugins: 'responsive',
      responsiveConfig: {
        'width < 1280 || height < 500': {
          flex: 1,
          height: null,
          minHeight: 240
        },
        'width >= 1280 && height >= 500': {
          flex: 1,
          height: null,
          minHeight: 160
        }
      },
      items: [
        {
          xtype: 'response-chart',
          cls: 'comparison-chart',
          reference: 'xml3Chart',
          hidden: true,
          bind: {
            hidden: '{xml3ChartMessage}'
          }
        },
        {
          hidden: true,
          bind: {
            hidden: '{!xml3ChartMessage}',
            html: '<div class="yasmine-compare-msg">{xml3ChartMessage}</div>'
          }
        }
      ],
    }
  ]
});

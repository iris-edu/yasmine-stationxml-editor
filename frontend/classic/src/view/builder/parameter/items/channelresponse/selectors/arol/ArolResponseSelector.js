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


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.arol.ArolResponseSelector', {
  extend: 'Ext.tab.Panel',
  xtype: 'arol-response-selector',
  reference: 'arol-response-selector',
  requires: [
    'yasmine.view.xml.builder.parameter.items.channelresponse.arolselector.ArolResponseSelectorController',
    'yasmine.view.xml.builder.parameter.items.channelresponse.arolselector.ArolResponseSelectorModel',
    'yasmine.view.xml.builder.parameter.items.channelresponse.components.ResponseTextViewer'
  ],
  controller: 'arol-response-selector',
  viewModel: 'arol-response-selector',
  "keyMap": {
    "m": {
      handler: function() {
        this.getViewModel().set('debugMode',  !this.getViewModel().get('debugMode'));
      }
    }
  },
  items: [
    {
      layout: {
        type: 'hbox',
        align: 'stretch'
      },
      bind: {
        title: '{dataloggerStatus} Datalogger'
      },
      bodyPadding: 5,
      items: [
        {
          width: 280,
          bodyPadding: '0 10 0 0',
          autoScroll: true,
          reference: 'datalogger',
        },
        {
          flex: 1,
          layout: 'fit',
          items: [
            {
              xtype: 'fieldset',
              layout: {
                type: 'vbox',
                align: 'stretch'
              },
              bind: {
                title: '{dataloggerResponseTitle}',
              },
              items: [
                {
                  hidden: true,
                  bind: {
                    hidden: '{!dataloggerCompleted}',
                    html: '{dataloggerResultTitle}'
                  },
                },
                {
                  xtype: 'response-text-viewer',
                  bind: {
                    value: '{dataloggerPreview}'
                  }
                },
                {
                  flex: 1,
                  reference: 'datalogger_response',
                  html: '',
                  autoScroll: true,
                  listeners: {
                    element: 'el',
                    click: 'onDataloggerFileClick'
                  },
                  hidden: true,
                  bind: {
                    hidden: '{!debugMode}'
                  }
                },
                {
                  bodyPadding: '20 0 0 0',
                  bind: {
                    html: '{datalogger_file}',
                    hidden: '{!debugMode}'
                  },
                  hidden: true
                }
              ]
            }
          ]
        }
      ]
    },
    {
      layout: {
        type: 'hbox',
        align: 'stretch'
      },
      bind: {
        title: '{sensorStatus} Sensor'
      },
      bodyPadding: 5,
      items: [
        {
          width: 280,
          bodyPadding: '0 10 0 0',
          autoScroll: true,
          reference: 'sensor',
        },
        {
          flex: 1,
          layout: 'fit',
          items: [
            {
              xtype: 'fieldset',
              layout: {
                type: 'vbox',
                align: 'stretch'
              },
              bind: {
                title: '{sensorResponseTitle}',
              },
              items: [
                {
                  hidden: true,
                  bind: {
                    hidden: '{!sensorCompleted}',
                    html: '{sensorResultTitle}'
                  },
                },
                {
                  xtype: 'response-text-viewer',
                  bind: {
                    value: '{sensorPreview}'
                  }
                },
                {
                  flex: 1,
                  reference: 'sensor_response',
                  html: '',
                  autoScroll: true,
                  listeners: {
                    element: 'el',
                    click: 'onSensorFileClick'
                  },
                  hidden: true,
                  bind: {
                    hidden: '{!debugMode}'
                  }
                },
                {
                  bodyPadding: '20 0 0 0',
                  bind: {
                    html: '{sensor_file}',
                    hidden: '{!debugMode}'
                  },
                  hidden: true
                }
              ]
            }
          ]
        }
      ]
    },
    // Response
    {
      bind: {
        title: '{responseStatus} Response',
        disabled: '{!dataloggerCompleted || !sensorCompleted}'
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

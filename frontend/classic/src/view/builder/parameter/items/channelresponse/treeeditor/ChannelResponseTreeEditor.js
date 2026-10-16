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
* 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.ChannelResponseTreeEditor', {
  extend: 'Ext.panel.Panel',
  xtype: 'channel-response-tree-editor',
  reference: 'channel-response-tree-editor',
  requires: [
    'Ext.plugin.Responsive',
    'yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.tree.Tree',
    'yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.ValueEditor',
    'yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.AttributeEditor',
    'yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.ChannelResponseTreeEditorModel',
    'yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.ChannelResponseTreeEditorController',
    'yasmine.utils.ResponseSchemaUtil',
    'yasmine.utils.XmlNodeUtil'
  ],
  viewModel: 'channel-response-tree-editor',
  controller: 'channel-response-tree-editor',
  flex: 1,
  minHeight: 240,
  layout: {
    type: 'hbox',
    align: 'stretch'
  },
  plugins: 'responsive',
  responsiveConfig: {
    'width < 768 || height < 500': {
      layout: {type: 'vbox', align: 'stretch'}
    },
    'width >= 768 && height >= 500': {
      layout: {type: 'hbox', align: 'stretch'}
    }
  },

  cls: 'yasmine-panel-outline yasmine-response-tree-editor',

  items: [
    {
      flex: 1,
      xtype: 'panel',
      layout: 'fit',
      items: [
        {
          flex: 1,
          scrollable: true,
          autoScroll: true,
          cls: 'yasmine-response-tree',
          xtype: 'channel-response-tree',
          width: 400,
          minWidth: 0,
          reference: 'channelresponsetree'
        }
      ]
    },
    {
      xtype: 'container',
      layout: {
        type: 'vbox',
        pack: 'center',
        align: 'stretch'
      },
      width: 400,
      flex: 1,
      minWidth: 0,
      plugins: 'responsive',
      responsiveConfig: {
        'width < 768 || height < 500': {
          width: undefined
        },
        'width >= 768 && height >= 500': {
          width: 400
        }
      },
      items: [
        {
          xtype: 'channel-response-value-editor',
          reference: 'channel-response-value-editor',
          width: '100%',
          height: 105,
          hidden: true,
          bind: {
            hidden: '{!selectedResponseNode}'
          }
        },
        {
          xtype: 'channel-response-attribute-editor',
          reference: 'channel-response-attribute-editor',
          flex: 1,
          width: '100%',
          hidden: true,
          bind: {
            hidden: '{!selectedResponseNode}'
          }
        },
        {
          xtype: 'panel',
          html: '<div class="yasmine-empty-state">Select a response node to edit its value and attributes.</div>',
          hidden: true,
          bind: {
            hidden: '{selectedResponseNode}'
          }
        }
      ]
    }
  ]
});

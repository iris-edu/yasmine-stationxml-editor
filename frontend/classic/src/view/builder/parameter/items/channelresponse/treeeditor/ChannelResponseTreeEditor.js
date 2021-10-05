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


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.ChannelResponseTreeEditor', {
  extend: 'Ext.panel.Panel',
  xtype: 'channel-response-tree-editor',
  reference: 'channel-response-tree-editor',
  requires: [
    'yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.tree.Tree',
    'yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.ValueEditor',
    'yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.AttributeEditor',
    'yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.ChannelResponseTreeEditorModel',
    'yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.ChannelResponseTreeEditorController'
  ],
  viewModel: 'channel-response-tree-editor',
  controller: 'channel-response-tree-editor',
  layout: {
    type: 'hbox',
    align: 'stretch'
  },

  style: 'border: solid #d0d0d0 1px;',

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
          style: 'border-right: solid #d0d0d0 1px;',
          xtype: 'channel-response-tree',
          width: 400,
          reference: 'channelresponsetree'
        }
      ]
    },
    {
      xtype: 'container',
      layout: {
        type: 'vbox',
        pack: 'center',
        align: 'center'
      },
      width: 400,
      items: [
        {
          xtype: 'channel-response-value-editor',
          reference: 'channel-response-value-editor',
          width: 400,
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
          width: 400,
          hidden: true,
          bind: {
            hidden: '{!selectedResponseNode}'
          }
        },
        {
          xtype: 'panel',
          html: '<span style="font-size: x-large; font-weight: 700;">Please select a node</span>',
          hidden: true,
          bind: {
            hidden: '{selectedResponseNode}'
          }
        }
      ]
    }
  ]
});

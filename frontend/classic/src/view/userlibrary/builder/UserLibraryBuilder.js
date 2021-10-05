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


Ext.define('yasmine.view.userlibrary.builder.UserLibraryBuilder', {
  extend: 'Ext.panel.Panel',
  requires: [
    'yasmine.view.userlibrary.builder.UserLibraryBuilderModel',
    'yasmine.view.userlibrary.builder.UserLibraryBuilderController'
  ],
  xtype: 'userlibrary-builder',
  controller: 'userlibrary-builder',
  viewModel: 'userlibrary-builder',
  bind: {
    title: 'User Library Builder | {selectedLibrary.name}'
  },
  frame: true,
  layout: 'border',
  items: [
    {
      region: 'north',
      items: {
        xtype: 'segmentedbutton',
        padding: '5 5 5 5',
        items: [{
          itemId: `type_${yasmine.NodeTypeEnum.network}`,
          text: 'Networks Library',
          iconCls: 'x-fa fa-connectdevelop',
          pressed: true
        }, {
          itemId: `type_${yasmine.NodeTypeEnum.station}`,
          text: 'Stations Library',
          iconCls: 'x-fa fa-building-o',
        }, {
          itemId: `type_${yasmine.NodeTypeEnum.channel}`,
          text: 'Channels Library',
          iconCls: 'x-fa fa-rss',
        }],
        listeners: {
          toggle: 'onNodeTypeSelected'
        }
      }
    },
    {
      region: 'center',
      layout: 'hbox',
      items: [
        {
          xtype: 'userlibrary-children',
          flex: 2,
          margin: '0 5 5 5',
          style: {
            'border': '2px solid #d0d0d0;'
          },
          width: '100%',
          height: '100%'
        },
        {
          reference: 'parameter-editor',
          xtype: 'parameter-list',
          margin: '0 5 5 0',
          style: {
            'border': '2px solid #d0d0d0;'
          },
          hideTitle: true,
          flex: 1,
          height: '100%',
        }
      ]
    }]
});

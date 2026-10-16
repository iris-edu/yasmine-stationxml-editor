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
* 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
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
  frame: false,
  cls: 'yasmine-workspace yasmine-library-workspace',
  layout: 'border',
  items: [
    {
      region: 'north',
      border: false,
      layout: {
        type: 'vbox',
        align: 'stretch'
      },
      items: [
        {
          xtype: 'toolbar',
          itemId: 'libraryTypeBar',
          cls: 'yasmine-wrap-toolbar',
          padding: '5 5 5 5',
          items: [{
            xtype: 'segmentedbutton',
            reference: 'libraryTypeSwitcher',
          cls: 'yasmine-library-type-switcher',
            items: [{
              itemId: `type_${yasmine.NodeTypeEnum.network}`,
            text: 'Networks',
            tooltip: 'Network templates',
              iconCls: 'x-fa fa-connectdevelop',
              pressed: true
            }, {
              itemId: `type_${yasmine.NodeTypeEnum.station}`,
            text: 'Stations',
            tooltip: 'Station templates',
              iconCls: 'x-fa fa-building-o',
            }, {
              itemId: `type_${yasmine.NodeTypeEnum.channel}`,
            text: 'Channels',
            tooltip: 'Channel templates',
              iconCls: 'x-fa fa-rss',
            }],
            listeners: {
              toggle: 'onNodeTypeSelected'
            }
          }]
        },
        {
          xtype: 'toolbar',
          itemId: 'libraryPaneBar',
          hidden: true,
          padding: '0 5 5 5',
          items: [{
            xtype: 'segmentedbutton',
            reference: 'libraryPaneSwitcher',
            allowMultiple: false,
            items: [
              {text: 'Hierarchy', itemId: 'hierarchy', pressed: true},
              {text: 'Parameters', itemId: 'detail'}
            ],
            listeners: {
              toggle: 'onLibraryPaneToggle'
            }
          }]
        }
      ]
    },
    {
      region: 'center',
      reference: 'libraryWorkspace',
      layout: {
        type: 'hbox',
        align: 'stretch'
      },
      items: [
        {
          xtype: 'userlibrary-children',
          reference: 'libraryChildren',
          flex: 2,
          minWidth: 200,
          margin: '0 0 5 5',
          cls: 'yasmine-panel-outline'
        },
        {
          reference: 'parameter-editor',
          xtype: 'parameter-list',
          margin: '0 5 5 0',
          cls: 'yasmine-panel-outline',
          hideTitle: true,
          flex: 1,
          minWidth: 220,
          // Splitter sits immediately before Parameters and drags horizontally.
          split: {
            side: 'before',
            collapseOnDblClick: false,
            collapsible: false
          }
        }
      ]
    }]
});

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


Ext.define('yasmine.view.xml.builder.children.card.ChildrenCard', {
  extend: 'Ext.panel.Panel',
  xtype: 'children-card',
  requires: [
    'yasmine.view.xml.builder.children.card.ChildrenCardController',
    'yasmine.view.xml.builder.children.card.ChildrenCardModel',
  ],
  viewModel: 'children-card',
  controller: 'children-card',
  layout: 'fit',
  items: [
    {
      xtype: 'dataview',
      loadMask: false,
      bind: {
        store: '{childrenStore}',
        selection: '{selectedItem}'
      },
      tpl: Ext.create('Ext.XTemplate',
        '<tpl for=".">',
        '<div class="phone  x-unselectable" style="border-color: {locationColor}',
        '<tpl if="last">',
        '; clear: both;',
        '</tpl>',
        '<tpl if="type == \'back\'">',
        '; height: 68px;',
        '</tpl>',
        '">',
        '<tpl if="type == \'node\'">',
        '<div><b>Code: </b> <span style="color: black;">{name}</span></div>',
        '<div><b>Start: </b> <span style="color: black;">{start:date(yasmine.Globals.DatePrintShortFormat)}</span></div>',
        '<div><b>End: </b> <span style="color: black;">{end:date(yasmine.Globals.DatePrintShortFormat)}</span></div>',
        '</tpl>',
        '<tpl if="nodeType == 1">',
        '<div><b>Description: </b><span style="color: black;">{description}</span></div>',
        '</tpl>',
        '<tpl if="nodeType == 2">',
        '<div><b>Longitude: </b> <span style="color: black;">{longitude}</span></div>',
        '<div><b>Latitude: </b> <span style="color: black;">{latitude}</span></div>',
        '<div><b>Site: </b> <span style="color: black;">{site}</span></div>',
        '</tpl>',
        '<tpl if="nodeType == 3">',
        '<div><b>Sample Rate: </b> <span style="color: black;">{sampleRate}</span></div>',
        '<div><b>Sensor: </b> <span style="color: black;">{sensor}</span></div>',
        '</tpl>',
        '<tpl if="has_children == true">',
        '<div><b>Click To Expand</b></div>',
        '</tpl>',
        '<tpl if="type == \'back\'">',
        '<i class="fa fa-chevron-circle-left fa-5x" style="color: #5fa2dd; padding-left: 37px;" aria-hidden="true"></i>',
        '</tpl>',
        '</div>',
        '</tpl>'
      ),
      id: 'phones',
      scrollable: true,
      itemSelector: 'div.phone',
      listeners: {
        beforeselect: 'onBeforeSelect',
        itemclick: 'onItemClick',
        itemdblclick: 'onItemDblClick',
        selectionchange: 'onItemSelectionChange',
        itemkeyup: 'onItemKeyUp'
      }
    }
  ]
});

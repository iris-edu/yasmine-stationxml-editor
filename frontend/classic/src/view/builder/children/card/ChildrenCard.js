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
* 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
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
      loadMask: true,
      bind: {
        store: '{childrenStore}',
        selection: '{selectedItem}'
      },
      tpl: Ext.create('Ext.XTemplate',
        '<tpl for=".">',
        '<div class="phone yasmine-node-card x-unselectable',
        '<tpl if="type == \'back\'"> yasmine-node-card-back-item</tpl>',
        '"',
        '<tpl if="locationColor"> style="border-left-color: {locationColor}"</tpl>',
        '>',
        '<tpl if="type == \'node\'">',
        '<div class="yasmine-node-card-title">{[this.text(values.name)]}</div>',
        '<div><b>Start</b><span>{[this.displayDate(values.start)]}</span></div>',
        '<div><b>End</b><span>{[this.displayDate(values.end)]}</span></div>',
        '</tpl>',
        '<tpl if="nodeType == 1">',
        '<div><b>Description</b><span>{[this.text(values.description)]}</span></div>',
        '</tpl>',
        '<tpl if="nodeType == 2">',
        '<div><b>Longitude</b><span>{[this.text(values.longitude)]}</span></div>',
        '<div><b>Latitude</b><span>{[this.text(values.latitude)]}</span></div>',
        '<div><b>Site</b><span>{[this.text(values.site)]}</span></div>',
        '</tpl>',
        '<tpl if="nodeType == 3">',
        '<div><b>Sample rate</b><span>{[this.text(values.sampleRate)]}</span></div>',
        '<div><b>Sensor</b><span>{[this.text(values.sensor)]}</span></div>',
        '</tpl>',
        '<tpl if="has_children == true">',
        '<div class="yasmine-node-card-hint">Open children</div>',
        '</tpl>',
        '<tpl if="type == \'back\'">',
        '<i class="x-fa fa-arrow-left yasmine-node-card-back" aria-hidden="true"></i>',
        '</tpl>',
        '</div>',
        '</tpl>',
        {
          displayDate: function (value) {
            return Ext.String.htmlEncode(yasmine.utils.DateUtil.formatShort(value) || '');
          },
          text: function (value) {
            return Ext.String.htmlEncode(value == null ? '' : String(value));
          }
        }
      ),
      id: 'phones',
      cls: 'yasmine-node-cards',
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

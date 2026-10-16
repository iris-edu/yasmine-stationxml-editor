/* ****************************************************************************
* 2026-09-24, version 4.3.0-beta: ASGSR, Alexey Emanov
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
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.nrl.NrlResponseTypeSelector', {
  extend: 'Ext.panel.Panel',
  xtype: 'nrl-response-type-selector',
  reference: 'nrl-response-type-selector',
  requires: [
    'Ext.plugin.Responsive'
  ],
  cls: 'yasmine-selectors yasmine-panel-outline yasmine-response-library-selectors',
  // Match SelectorsContainer: type cards must be direct body children.
  // A nested hbox wrapper is clipped by compact/card CSS (height:100% on
  // every .x-box-inner), which left only "Select a response type." visible.
  layout: {
    type: 'hbox',
    align: 'center',
    pack: 'center'
  },
  plugins: 'responsive',
  responsiveConfig: {
    'width < 768 || height < 500': {
      layout: {type: 'vbox', align: 'stretch', pack: 'center'}
    },
    'width >= 768 && height >= 500': {
      layout: {type: 'hbox', align: 'center', pack: 'center'}
    }
  },
  bodyPadding: 12,
  dockedItems: [{
    xtype: 'component',
    dock: 'top',
    html: '<b>Select a response type.</b>',
    padding: '12 12 0 12',
    style: {textAlign: 'center'}
  }],
  defaults: {
    xtype: 'button',
    margin: 8,
    cls: 'library-btn library-btn-multiline yasmine-response-library-card',
    width: 150,
    maxWidth: 220,
    height: 150
  },
  items: [
    {
      text: 'Datalogger<br>+ sensor',
      handler: function (button) {
        button.up('yasmine-channel-response-field').getController().openNrlSelector('cascade');
      }
    },
    {
      text: 'Integrated',
      handler: function (button) {
        button.up('yasmine-channel-response-field').getController().openNrlSelector('integrated');
      }
    },
    {
      text: 'SOH',
      handler: function (button) {
        button.up('yasmine-channel-response-field').getController().openNrlSelector('soh');
      }
    }
  ]
});

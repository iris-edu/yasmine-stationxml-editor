/* ****************************************************************************
* 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
* 2026-10-04, version 4.4.0-beta: ASGSR, Alexey Emanov
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
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.selectors.SelectorsContainer', {
  extend: 'Ext.panel.Panel',
  xtype: 'selectors-container',
  reference: 'selectors-container',
  requires: [
    'Ext.plugin.Responsive'
  ],
  // Four cards need ~660px in a row; stack below lg so tablets do not clip.
  cls: 'yasmine-selectors yasmine-panel-outline yasmine-response-library-selectors',
  layout: {
    type: 'hbox',
    align: 'center',
    pack: 'center'
  },
  scrollable: 'y',
  plugins: 'responsive',
  responsiveConfig: {
    'width < 1024 || height < 500': {
      layout: {type: 'vbox', align: 'stretch', pack: 'center'}
    },
    'width >= 1024 && height >= 500': {
      layout: {type: 'hbox', align: 'center', pack: 'center'}
    }
  },
  bodyPadding: 12,
  defaults: {
    xtype: 'button',
    margin: 8,
    cls: 'library-btn yasmine-response-library-card',
    width: 150,
    maxWidth: 220,
    height: 150
  },
  items: [
  {
    text: 'NRL<br>Offline',
    cls: 'library-btn library-btn-multiline yasmine-response-library-card',
    handler: 'createNrlResponseSelector'
  },
  {
    text: 'AROL',
    cls: 'library-btn yasmine-response-library-card',
    handler: 'createArolResponseSelector'
  },
  {
    text: 'NRL<br>Online',
    reference: 'nrlv2OnlineBtn',
    cls: 'library-btn library-btn-multiline yasmine-response-library-card',
    handler: 'createNrlv2ResponseSelector',
    bind: {
      disabled: '{!nrlv2OnlineEnabled}',
      tooltip: '{nrlv2OnlineTooltip}'
    }
  },
  {
    text: 'Upload<br>RESP',
    cls: 'library-btn library-btn-multiline yasmine-response-library-card',
    handler: 'createRespUploadSelector'
  }
]
});




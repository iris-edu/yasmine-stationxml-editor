/* ****************************************************************************
* 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
*
* This file is part of the yasmine editing tool.
*
* yasmine (Yet Another Station Metadata INformation Editor), a tool to
* create and edit station metadata information in FDSN stationXML format,
* is a common development of IRIS and RESIF.
* Development and addition of new features is shared and agreed between
* IRIS and RESIF.
*
* This program is free software; you can redistribute it
* and/or modify it under the terms of the GNU Lesser General Public
* License as published by the Free Software Foundation; either
* version 3 of the License, or (at your option) any later version.
*
* ****************************************************************************/


Ext.define('yasmine.model.CollectionItem', {
  extend: 'Ext.data.Model',
  requires: [
    'Ext.data.identifier.Negative'
  ],
  idProperty: '_extRecordId',
  identifier: 'negative',
  fields: [
    {name: '_extRecordId', type: 'int', persist: false}
  ]
});

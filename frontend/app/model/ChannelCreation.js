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


Ext.define('yasmine.model.ChannelCreation', {
  extend: 'Ext.data.Model',
  proxy: {
    type: 'rest',
    url: '/api/wizard/channel/',
    writer: {
      type: 'json',
      writeAllFields: true
    }
  },
  fields: [
    {name: 'id', type: 'int'},
    {name: 'xmlId', type: 'int'},
    {name: 'code1', type: 'string'},
    {name: 'code2', type: 'string'},
    {name: 'code3', type: 'string'},
    {name: 'chn_code2', type: 'string'},
    {name: 'chn_code3', type: 'string'},
    {name: 'location_code', type: 'string'},
    {name: 'latitude', type: 'number'},
    {name: 'longitude', type: 'number'},
    {name: 'elevation', type: 'number'},
    {name: 'depth', type: 'number'},
    {name: 'azimuth1', type: 'number'},
    {name: 'azimuth2', type: 'number'},
    {name: 'azimuth3', type: 'number'},
    {name: 'dip1', type: 'number'},
    {name: 'dip2', type: 'number'},
    {name: 'dip3', type: 'number'},
    {name: 'start_date', type: 'date', dateFormat: 'd/m/Y H:i:s'},
    {name: 'end_date', type: 'date', dateFormat: 'd/m/Y H:i:s'},
    {name: 'stationNodeId', type: 'int'},
    {name: 'sensorKeys'},
    {name: 'dataloggerKeys'},
    {name: 'libraryType'},
    {
      name: 'summary', type: 'string', persist: false,
      depends: ['location_code', 'latitude', 'longitude', 'elevation', 'depth', 'libraryType', 'dataloggerKeys', 'sensorKeys'],
      convert: function(value, record) {
        return `
        Location Code: ${record.get('location_code')},
        Latitude: ${record.get('latitude')},
        Longitude: ${record.get('longitude')},
        Elevation: ${record.get('elevation')},
        Depth: ${record.get('depth')},
        Library Type: ${record.get('libraryType')},
        Datalogger Keys: ${record.get('dataloggerKeys')},
        Sensor Keys: ${record.get('sensorKeys')}
        `;
      }
    },
  ]
});

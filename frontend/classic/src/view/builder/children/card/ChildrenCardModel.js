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


Ext.define('yasmine.view.xml.builder.children.card.ChildrenCardModel', {
  extend: 'Ext.app.ViewModel',
  alias: 'viewmodel.children-card',
  data: {
    selectedItem: null,
    parentNodeId: 0
  },
  stores: {
    childrenStore: {
      storeId: 'childrenStore',
      model: 'yasmine.view.xml.builder.children.card.Item',
      autoLoad: true,
      proxy: {
        type: 'rest',
        url: '/api/xml/tree/{xmlId}/{parentNodeId}',
        paramsAsJson: true
      },
      remoteFilter: true
    }
  },
});

Ext.define('yasmine.view.xml.builder.children.card.Item', {
  extend: 'Ext.data.Model',
  fields: [
    { name: 'name', type: 'string' },
    { name: 'type', type: 'string', defaultValue: 'node' },
    {
      name: 'locationColor', type: 'string', convert: function (v, record) {
        let locationCode = record.get('location_code');
        return (locationCode) ? yasmine.Globals.LocationColorScale(locationCode) : '#e4e4e4';
      }
    },
    { name: 'parentId', type: 'int' },
    {
      name: 'description', type: 'string', convert: function (v, record) {
        var desc = record.get('description');
        return desc ? desc : yasmine.Globals.NotApplicable
      }
    },
    { name: 'start', type: 'date', dateFormat: yasmine.Globals.DateReadFormat },
    { name: 'end', type: 'date', dateFormat: yasmine.Globals.DateReadFormat },
    {
      name: 'iconCls', type: 'string', persist: false,
      depends: ['nodeType'],
      convert: function (value, record) {
        if (record.get('root')) {
          return 'fa-file-code-o';
        }
        return yasmine.utils.NodeTypeConverter.toIcon(record.get('nodeType'))
      }
    },
    { name: 'nodeType', type: 'int', persist: false },
    {
      name: 'nodeTypeName', type: 'string', persist: false, depends: ['nodeType'],
      convert: function (value, record) {
        return yasmine.utils.NodeTypeConverter.toString(record.get('nodeType'));
      }
    },
    { name: 'longitude', persist: false },
    { name: 'latitude', persist: false },
    { name: 'site', persist: false },
    { name: 'sampleRate', persist: false, mapping: 'sample_rate' },
    { name: 'sensor', persist: false },
    { name: 'last', persist: false },
    { name: 'has_children', persist: false, type: 'boolean' }
  ]
});

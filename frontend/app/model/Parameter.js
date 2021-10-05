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


Ext.define('yasmine.model.Parameter', {
  extend: 'Ext.data.Model',
  proxy: {
    type: 'rest',
    url: '/api/xml/attr/',
    reader: {
      type: 'json',
      rootProperty: 'data',
      totalProperty: 'totalCount'
    },
    writer: {
      nameProperty: 'mapping'
    }
  },
  fields: [
    { name: 'id', type: 'int', persist: false },
    { name: 'required', type: 'boolean', persist: false },
    { name: 'sortIndex', type: 'int', mapping: 'attr_index', persist: false },
    { name: 'name', type: 'string', mapping: 'attr_name', persist: false },
    { name: 'class', type: 'string', mapping: 'attr_class', persist: false },
    { name: 'parameterId', type: 'int', mapping: 'attr_id' },
    { name: 'nodeId', type: 'int', mapping: 'node_inst_id' },
    { name: 'node_id', type: 'int', persist: false },
    {
      name: 'value',
      mapping: 'value_obj',
      convertOnSet: false,
      convert: function (value, record) {
        if (record.get('attr_class') == 'yasmine-date-field') {
          if (value) {
            if (typeof value === 'string') {
              return Ext.Date.parse(value, yasmine.Globals.DateReadFormat, true);
            } else if (value instanceof Date) {
              return value;
            }
          }
          return null;
        }
        return value
      },
      persist: true
    }, {
      name: 'isComplexType',
      convertOnSet: false,
      convert: function (v, record) {
        var attr_class = record.get('class')
        return !(attr_class == 'yasmine-text-field' ||
          attr_class == 'yasmine-text-help-field' ||
          attr_class == 'yasmine-longitude-field' ||
          attr_class == 'yasmine-latitude-field' ||
          attr_class == 'yasmine-int-field' ||
          attr_class == 'yasmine-float-field' ||
          attr_class == 'yasmine-date-field')
      }
    }]
});

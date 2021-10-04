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


Ext.define('yasmine.model.TreeItem', {
  extend: 'Ext.data.TreeModel',
  requires: ['yasmine.NodeTypeEnum'],
  fields: [
    {name: 'name', type: 'string', persist: false},
    {name: 'index', type: 'int', persist: false},
    {name: 'parentId', type: 'int', persist: false},
    {name: 'nodeType', type: 'int', persist: false},
    {
      name: 'leaf', type: 'boolean', persist: false,
      convert: function (value, record) {
        return !(record.get('has_children') || record.get('root'));
      }
    },
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
    {
      name: 'text', type: 'string', persist: false,
      depends: ['name'],
      convert: function (value, record) {
        if (record.get('id') === 0) {
          return record.get('text');
        }

        let dates = [];
        let start = record.get('start');
        if (start) {
          start = Ext.Date.parse(start, yasmine.Globals.DateReadFormat, true);
          dates.push(Ext.Date.format(start, yasmine.Globals.DatePrintShortFormat));
        }

        let end = record.get('end');
        if (end) {
          end = Ext.Date.parse(end, yasmine.Globals.DateReadFormat, true);
          dates.push(Ext.Date.format(end, yasmine.Globals.DatePrintShortFormat));
        }

        let dateStr = (dates.length > 0) ? `(${dates.join(' - ')})` : '';
        return `${record.get('name')} ${dateStr} <i>${record.get('description')}</i>`;
      }
    }
  ]
});

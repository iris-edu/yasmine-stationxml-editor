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
* 2019/10/07 : version 2.0.0 initial commit
* 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.parameter.items.comments.CommentsEditorModel', {
    extend: 'yasmine.view.xml.builder.parameter.ParameterItemEditorModel',
    alias: 'viewmodel.comments-editor',
    data: {
        selectedCommentRow: null
    },
    stores: {
        commentStore: {
            model: 'yasmine.view.xml.builder.parameter.items.comments.Comment',
            data: []
        }
    }
});

Ext.define('yasmine.view.xml.builder.parameter.items.comments.Comment', {
    extend: 'yasmine.model.CollectionItem',
    fields: [
        { name: 'id', type: 'int', allowNull: true, defaultValue: null },
        { name: 'value', defaultValue: null },
        { name: 'subject', defaultValue: null },
        { name: 'begin_effective_time', defaultValue: null },
        { name: 'end_effective_time', defaultValue: null },
        { name: 'authors', defaultValue: null },
        {
            name: 'beginEffectiveTime',
            persist: false,
            depends: ['begin_effective_time'],
            convert: function (value, record) {
                var date = record.get('begin_effective_time');
                if (!date) return null;
                var parsed = Ext.Date.parse(date, yasmine.Globals.DateReadFormat, true);
                return parsed || Ext.Date.parse(date, yasmine.Globals.DatePrintLongFormat, true);
            }
        },
        {
            name: 'endEffectiveTime',
            persist: false,
            depends: ['end_effective_time'],
            convert: function (value, record) {
                var date = record.get('end_effective_time');
                if (!date) return null;
                var parsed = Ext.Date.parse(date, yasmine.Globals.DateReadFormat, true);
                return parsed || Ext.Date.parse(date, yasmine.Globals.DatePrintLongFormat, true);
            }
        }
    ]
});

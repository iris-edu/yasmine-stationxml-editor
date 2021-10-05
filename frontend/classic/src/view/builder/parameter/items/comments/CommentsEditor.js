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


Ext.define('yasmine.view.xml.builder.parameter.items.comments.CommentsEditor', {
  extend: 'Ext.form.Panel',
  xtype: 'yasmine-comments-field',
  requires: [
    'yasmine.view.xml.builder.parameter.items.comments.CommentsEditorModel',
    'yasmine.view.xml.builder.parameter.items.comments.CommentsEditorController'
  ],
  viewModel: 'comments-editor',
  controller: 'comments-editor',
  items: [{
    bind: {
      html: '{validationErrors}',
      hidden: '{!canShowValidationError}'
    },
    hidden: true,
    width: '100%',
    padding: '5 8 5 8'
  }, {
    xtype: 'grid',
    flex: 1,
    width: 800,
    height: 400,
    style: 'border: solid #d0d0d0 1px',
    bind: {
      store: '{commentStore}',
      selection: '{selectedCommentRow}'
    },
    columns: [
      {
        header: 'Subject',
        dataIndex: 'subject',
        emptyCellText: yasmine.Globals.NotApplicable,
        flex: 1
      },
      {
        header: 'Comment',
        dataIndex: 'value',
        emptyCellText: yasmine.Globals.NotApplicable,
        flex: 1
      },
      {
        header: 'Effective Start Date',
        dataIndex: 'beginEffectiveTime',
        xtype: 'datecolumn',
        format: yasmine.Globals.DatePrintLongFormat,
        emptyCellText: yasmine.Globals.NotApplicable,
        flex: 1
      },
      {
        header: 'Effective End Date',
        dataIndex: 'endEffectiveTime',
        xtype: 'datecolumn',
        format: yasmine.Globals.DatePrintLongFormat,
        emptyCellText: yasmine.Globals.NotApplicable,
        flex: 1
      },
      {
        header: 'Authors',
        dataIndex: 'authors',
        flex: 1,
        emptyCellText: yasmine.Globals.NotApplicable,
        renderer: function (value) {
          if (!value ||
            value.length === 0) {
            return yasmine.Globals.NotApplicable;
          }
          let result = [];
          value.forEach(function (person) {
            if (person.names &&
              person.names.length > 0) {
              result = result.concat(person.names);
            }
            if (person.agencies &&
              person.agencies.length > 0) {
              result = result.concat(person.agencies);
            }
            if (person.emails &&
              person.emails.length > 0) {
              result = result.concat(person.emails);
            }
          });
          return result.join('; ');
        }
      }
    ],
    listeners: {
      itemdblclick: 'onEditClick'
    },
    tbar: [{
      iconCls: 'x-fa fa-plus',
      tooltip: 'Add Comment',
      handler: 'onAddClick'
    }, {
      iconCls: 'x-fa fa-minus',
      tooltip: 'Delete Comment',
      handler: 'onDeleteClick',
      disabled: true,
      bind: {
        disabled: '{!selectedCommentRow}'
      }
    }, {
      iconCls: 'x-fa fa-pencil',
      tooltip: 'Edit Comment',
      handler: 'onEditClick',
      disabled: true,
      bind: {
        disabled: '{!selectedCommentRow}'
      }
    }]
  }]
});

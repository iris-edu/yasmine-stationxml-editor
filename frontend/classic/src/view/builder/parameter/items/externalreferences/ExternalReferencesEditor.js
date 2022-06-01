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


Ext.define('yasmine.view.xml.builder.parameter.items.externalreferences.ExternalReferencesEditor', {
  extend: 'Ext.form.Panel',
  xtype: 'yasmine-external-references-field',
  requires: ['yasmine.view.xml.builder.parameter.items.externalreferences.ExternalReferencesEditorModel',
    'yasmine.view.xml.builder.parameter.items.externalreferences.ExternalReferencesEditorController'],
  viewModel: 'external-references-editor',
  controller: 'external-references-editor',
  border: true,
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
    reference: 'referencegrid',
    width: 700,
    height: 400,
    plugins: [{
      ptype: 'rowediting',
      clicksToMoveEditor: 1
    }],
    selModel: 'rowmodel',
    bind: {
      store: '{dataStore}',
      selection: '{theRow}'
    },
    columns: [{
      header: 'Uri',
      dataIndex: 'uri',
      width: 250,
      editor: 'textfield'
    }, {
      header: 'Description',
      dataIndex: 'description',
      flex: 1,
      editor: 'textfield'
    }],
    tbar: [{
      xtype: 'button',
      iconCls: 'x-fa fa-plus',
      tooltip: 'Create',
      handler: 'onAddClick'
    }, {
      xtype: 'button',
      iconCls: 'x-fa fa-minus',
      tooltip: 'Delete',
      handler: 'onDeleteClick',
      disabled: true,
      bind: {
        disabled: '{!theRow}'
      }
    }]
  }]
});

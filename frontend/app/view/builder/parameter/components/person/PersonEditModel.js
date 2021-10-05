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


Ext.define('yasmine.view.xml.builder.parameter.components.person.PersonEditModel', {
  extend: 'Ext.app.ViewModel',
  alias: 'viewmodel.person-edit',
  data: {
    selectedNameRow: null,
    selectedAgencyRow: null,
    selectedEmailRow: null,
    selectedPhoneRow: null,

    person: null,

    parameterId: null,
    nodeTypeId: null
  },
  stores: {
    agencyHelpStore: {
      model: 'yasmine.view.xml.builder.parameter.components.person.AgencyHelper',
      type: 'json',
      proxy: {
        type: 'rest',
        url: '/api/helper/{nodeTypeId}/{parameterId}'
      },
      sorters: [{
        property: 'value',
        direction: 'ASC'
      }],
      filters: [{
        property: '$component',
        value: 'agency'
      }],
      remoteFilter: false,
      autoLoad: true
    },
    nameStore: {
      model: 'yasmine.view.xml.builder.parameter.components.person.Name',
      data: []
    },
    agencyStore: {
      model: 'yasmine.view.xml.builder.parameter.components.person.Agency',
      data: []
    },
    emailStore: {
      model: 'yasmine.view.xml.builder.parameter.components.person.Email',
      data: []
    },
    phoneStore: {
      model: 'yasmine.view.xml.builder.parameter.components.person.Phone',
      data: []
    }
  }
});

Ext.define('yasmine.view.xml.builder.parameter.components.person.AgencyHelper', {
  extend: 'Ext.data.Model',
  fields: [
    { name: 'acromyn', type: 'string' },
    { name: 'name', type: 'string' },
    { name: 'website', type: 'string' },
    {
      name: 'searchText',
      persist: false,
      depends: ['acromyn'],
      convert: function (value, record) {
        return `${record.get('acromyn')} ${record.get('name')} ${record.get('website')}`;
      }
    }
  ]
});

Ext.define('yasmine.view.xml.builder.parameter.components.person.Name', {
  extend: 'Ext.data.Model',
  fields: [
    { name: '_name', type: 'string' }
  ]
});

Ext.define('yasmine.view.xml.builder.parameter.components.person.Agency', {
  extend: 'Ext.data.Model',
  fields: [
    { name: '_name', type: 'string' }
  ]
});

Ext.define('yasmine.view.xml.builder.parameter.components.person.Email', {
  extend: 'Ext.data.Model',
  fields: [
    { name: '_email', type: 'string' }
  ]
});

Ext.define('yasmine.view.xml.builder.parameter.components.person.Phone', {
  extend: 'Ext.data.Model',
  fields: [
    { name: '_country_code', type: 'int' },
    { name: '_area_code', type: 'int' },
    { name: '_phone_number', type: 'string' },
    { name: '_description', type: 'string' }
  ]
});

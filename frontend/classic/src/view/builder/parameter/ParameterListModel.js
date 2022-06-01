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


Ext.define('yasmine.view.xml.builder.parameter.ParameterListModel', {
  extend: 'Ext.app.ViewModel',
  alias: 'viewmodel.parameter-list',
  requires: ['yasmine.model.Parameter', 'yasmine.NodeTypeEnum'],
  data: {
    nodeId: null,
    nodeType: null,
    selectedAvailableParameter: null,
    theRow: null
  },
  stores: {
    infoStore: {
      model: 'yasmine.model.Parameter',
      pageSize: 0,
      autoLoad: false,
      autoSync: false,
      remoteFilter: true,
      filters: [{
        property: 'node_inst_id',
        value: '{nodeId}'
      }],
      sorters: [{
        property: 'required',
        direction: 'DESC'
      }, {
        property: 'sortIndex',
        direction: 'ASC'
      }, {
        property: 'name',
        direction: 'ASC'
      }]
    },
    availableParamsStore: {
      type: 'json',
      proxy: {
        type: 'rest',
        url: '/api/xml/attr/available/{nodeId}'
      },
      sorters: [{
        property: 'name',
        direction: 'ASC'
      }],
      remoteFilter: false,
      autoLoad: false
    }
  },
  formulas: {
    hideTitle: function (get) {
      return this.getView().config.hideTitle
    },
    title: function (get) {
      if (this.getView().config.hideTitle) {
        return '';
      }
      var type = get('nodeType');
      if (type === yasmine.NodeTypeEnum.network) {
        return 'Network Information';
      }
      if (type === yasmine.NodeTypeEnum.station) {
        return 'Station Information';
      }
      if (type === yasmine.NodeTypeEnum.channel) {
        return 'Channel Information';
      }
      return 'Please select a node';
    },
    isAvailableParamsEnabled: function (get) {
      return get('nodeType') != null;
    }
  }
});

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


Ext.define('yasmine.view.settings.SettingsListModel', {
  extend: 'Ext.app.ViewModel',
  alias: 'viewmodel.settings',
  data: {
    settings: null
  },
  stores: {
    networkDefaultFields: {
      autoLoad: true,
      proxy: {
        type: 'rest',
        url: `/api/attr/${yasmine.NodeTypeEnum.network}`,
        paramsAsJson: true
      }
    },
    stationDefaultFields: {
      autoLoad: true,
      proxy: {
        type: 'rest',
        url: `/api/attr/${yasmine.NodeTypeEnum.station}`,
        paramsAsJson: true
      }
    },
    channelDefaultFields: {
      autoLoad: true,
      proxy: {
        type: 'rest',
        url: `/api/attr/${yasmine.NodeTypeEnum.channel}`,
        paramsAsJson: true
      }
    }
  }
});

Ext.define('yasmine.view.settings.Settings', {
  extend: 'Ext.data.Model',
  proxy: {
    type: 'rest',
    url: '/api/cfg/',
    writer: {
      type: 'json',
      writeAllFields: false
    }
  },
  fields: [
    {name: 'id', type: 'int'},
    {name: 'general__date_format_long', type: 'string'},
    {name: 'general__date_format_short', type: 'string'},
    {name: 'general__module', type: 'string'},
    {name: 'general__source', type: 'string'},
    {name: 'general__uri', type: 'string'},
    {name: 'general__user_library_source_url', type: 'string'},
    {name: 'general__xml_view_mode', type: 'int'},
    {name: 'network__code', type: 'string'},
    {name: 'network__num_stations', type: 'int'},
    {name: 'network__required_fields'},
    {name: 'station__code', type: 'string'},
    {name: 'station__num_channels', type: 'int'},
    {name: 'station__required_fields'},
    {name: 'station__spread_to_channels'},
    {name: 'channel__code', type: 'string'},
    {name: 'channel__required_fields'}
  ]
});

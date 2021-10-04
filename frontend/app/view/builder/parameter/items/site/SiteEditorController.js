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


Ext.define('yasmine.view.xml.builder.parameter.items.site.SiteEditorController', {
  extend: 'yasmine.view.xml.builder.parameter.ParameterItemEditorController',
  alias: 'controller.site-editor',
  initData: function () {
    let record = this.getViewModel().get('record');
    this.getViewModel().set('nodeId', record.get('node_type_id'));
    this.getViewModel().set('attrId', record.get('parameterId'));
    this.getViewModel().notify();

    let value = record.get('value');
    if (!value) {
      return;
    }

    this.getViewModel().set('name', value.name);
    this.getViewModel().set('town', value.town);
    this.getViewModel().set('description', value.description);
    this.getViewModel().set('county', value.county);
    this.getViewModel().set('region', value.region);
    this.getViewModel().set('country', value.country);
  },
  fillRecord: function () {
    let viewModel = this.getViewModel();
    let value = {
      'py/object': 'obspy.core.inventory.util.Site',
      name: viewModel.get('name'),
      town: viewModel.get('town'),
      description: viewModel.get('description'),
      county: viewModel.get('county'),
      region: viewModel.get('region'),
      country: viewModel.get('country')
    };

    viewModel.get('record').set('value', value);
  },
  onGatitoSelect: function (combo, record) {
    this.getViewModel().set('name', record.get('Name'));
    this.getViewModel().set('town', record.get('Town'));
    this.getViewModel().set('description', record.get('Description'));
    this.getViewModel().set('county', record.get('County'));
    this.getViewModel().set('region', record.get('Region'));
    this.getViewModel().set('country', record.get('Country'));
    this.getViewModel().notify();
  }
});

/* ****************************************************************************
*
* This file is part of the yasmine editing tool.
*
* yasmine (Yet Another Station Metadata INformation Editor), a tool to
* create and edit station metadata information in FDSN stationXML format,
* is a common development of IRIS and RESIF.
* Development and addition of new features is shared and agreed between * IRIS and RESIF.
*
* Version 1.0 of the software was funded by SAGE, a major facility fully
* funded by the National Science Foundation (EAR-1261681-SAGE),
* development done by ISTI and led by IRIS Data Services.
* Version 2.0 of the software was funded by CNRS and development led by * RESIF.
*
* This program is free software; you can redistribute it
* and/or modify it under the terms of the GNU Lesser General Public
* License as published by the Free Software Foundation; either
* version 3 of the License, or (at your option) any later version.
*
* This program is distributed in the hope that it will be
* useful, but WITHOUT ANY WARRANTY; without even the implied warranty
* of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
* GNU Lesser General Public License (GNU-LGPL) for more details.
*
* You should have received a copy of the GNU Lesser General Public
* License along with this software. If not, see
* <https://www.gnu.org/licenses/>
*
*
* 2019/10/07 : version 2.0.0 initial commit
* 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.parameter.items.measurement.MeasurementMetadataWindowController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.measurement-metadata-window',

  requires: [
    'yasmine.view.xml.builder.parameter.items.measurement.MeasurementMetadata'
  ],

  initData: function (record, nodeType) {
    var helper = yasmine.view.xml.builder.parameter.items.measurement.MeasurementMetadata;
    var definition = helper.getDefinition(record.get('name'));
    var metadata = helper.normalize(record.get('name'), record.get('valueMeta'));
    var spreadAllowed = nodeType === yasmine.NodeTypeEnum.station &&
      Ext.Array.contains(['latitude', 'longitude', 'elevation'], record.get('name'));
    var settings = yasmine.Globals.Settings || {};

    this.originalMetadata = record.get('valueMeta');
    this.getView().stationXmlHelpContext = {
      nodeType: nodeType,
      parameterName: record.get('name')
    };
    this.getViewModel().set({
      record: record,
      fieldLabel: definition.label,
      plusError: metadata.plus_error,
      minusError: metadata.minus_error,
      measurementMethod: metadata.measurement_method,
      datum: metadata.datum,
      unit: metadata.unit,
      showDatum: !!definition.hasDatum,
      unitReadOnly: !!definition.fixedUnit,
      spreadAllowed: spreadAllowed,
      spreadToChannels: spreadAllowed && !!settings.station__spread_to_channels
    });
  },

  collectMetadata: function () {
    var viewModel = this.getViewModel();
    return {
      plus_error: viewModel.get('plusError'),
      minus_error: viewModel.get('minusError'),
      measurement_method: viewModel.get('measurementMethod') || null,
      datum: viewModel.get('showDatum') ? (viewModel.get('datum') || null) : null,
      unit: viewModel.get('unit') || null
    };
  },

  persistMetadata: function (metadata) {
    var me = this;
    var viewModel = this.getViewModel();
    var record = viewModel.get('record');
    var proxy = record.getProxy();
    var spread = viewModel.get('spreadAllowed') &&
      viewModel.get('spreadToChannels');

    record.set('valueMeta', metadata);

    if (record.phantom && (record.get('value') == null || record.get('value') === '')) {
      this.getView().fireEvent('metadataSaved', record, false);
      this.closeView();
      return;
    }

    proxy.extraParams = {spread_to_channels: spread};
    record.save({
      success: function () {
        proxy.extraParams = {};
        me.getView().fireEvent('metadataSaved', record, true);
        me.closeView();
      },
      failure: function () {
        proxy.extraParams = {};
        record.set('valueMeta', me.originalMetadata);
      }
    });
  },

  onSaveClick: function () {
    if (!this.getView().down('form').getForm().isValid()) {
      return;
    }
    this.persistMetadata(this.collectMetadata());
  },

  onClearClick: function () {
    this.persistMetadata(null);
  },

  onCancelClick: function () {
    this.closeView();
  }
});

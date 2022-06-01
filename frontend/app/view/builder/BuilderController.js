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


Ext.define('yasmine.view.xml.builder.BuilderController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.builder',
  requires: [
    'yasmine.view.xml.builder.parameter.ParameterList',
    'yasmine.view.xml.builder.comparison.Comparison'
  ],
  onTreeItemSelected: function(node) {
    this.getViewModel().set('selectedNode', node);
  },
  onTreeItemDeSelected: function() {
    this.getViewModel().set('selectedNode', null);
  },
  onShowParameters: function(node) {
    this.getViewModel().set('selectedNode', node);
  },
  afterRender: function () {
    let viewModel = this.getViewModel();
    let xmlId = viewModel.get('xmlId');
    viewModel.set('xml', yasmine.model.Xml.load(parseInt(xmlId)));
    let mode = this.getViewModel().get('viewMode');
    if (mode === yasmine.BuilderMode.BUILDER) {
      this.buildBuilderModeView()
    } else {
      this.buildComparisonModeView()
    }
  },
  onExportXmlClick: function () {
    yasmine.store.FileLoader.load(`api/xml/ie/${this.getViewModel().get('xmlId')}`);
  },
  onValidateXmlClick: function () {
    Ext.Ajax.request({
      url: `/api/xml/validate/${this.getViewModel().get('xmlId')}`,
      method: 'GET',
      success: function (response) {
        var errors = JSON.parse(response.responseText);
        if (errors && errors.length > 0) {
          Ext.Msg.alert('Validation Errors', errors.join('<br>'), Ext.emptyFn);
        } else {
          Ext.Msg.alert('Validation Errors', 'No Errors', Ext.emptyFn);
        }
      }
    });
  },
  buildBuilderModeView: function () {
    this.getViewModel().set('viewMode', yasmine.BuilderMode.BUILDER);
    this.removeModeView('xml-comparison');
    this.createModeView('parameter-list', '40%');
  },
  buildComparisonModeView: function () {
    this.getViewModel().set('viewMode', yasmine.BuilderMode.COMPARATOR);
    this.removeModeView('parameter-list');
    this.createModeView('xml-comparison', '70%');
  },
  removeModeView: function (viewName) {
    let view = this.lookup(viewName);
    if (view) {
      this.getView().remove(view);
    }
  },
  createModeView: function (viewName, viewWidth) {
    let modeView = Ext.create({
      xtype: viewName,
      reference: viewName,
      region: 'east',
      width: viewWidth
    });

    this.getView().add(modeView);
    let selectedNode = this.getViewModel().get('selectedNode');
    if (selectedNode) {
      modeView.getController().initData(selectedNode);
    }
  }
});

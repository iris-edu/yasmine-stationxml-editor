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


Ext.define('yasmine.view.xml.builder.parameter.ParameterEditorControllerExt', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.parameter-editor-ext',
  requires: [
    'yasmine.view.xml.builder.parameter.items.text.TextEditor',
    'yasmine.view.xml.builder.parameter.items.int.IntEditor',
    'yasmine.view.xml.builder.parameter.items.float.FloatEditor',
    'yasmine.view.xml.builder.parameter.items.latitude.LatitudeEditor',
    'yasmine.view.xml.builder.parameter.items.longitude.LongitudeEditor',
    'yasmine.view.xml.builder.parameter.items.date.DateEditor'
  ],
  createFrom: function () {
    var record = this.getViewModel().get('record');
    var content = Ext.create({
      fieldLabel: Ext.String.capitalize(record.get('name')),
      xtype: record.get('class'),
      reference: 'contentView',
      value: record.get('value')
    });
    this.getView().down('form').insert(0, content);
    content.getViewModel().set('record', record);

    this.getViewModel().set('station__spread_to_channels', yasmine.Globals.Settings.station__spread_to_channels)
    content.getViewModel().set('nodeType', this.getViewModel().get('nodeType'));
  },
  onSaveClick: function () {
    var contentView = this.lookupReference('contentView');
    var contentController = contentView.getController();
    var record = contentView.getViewModel().get('record');

    record.set('value', contentView.getValue(), {commit: false})

    if (contentController && contentController.validate && !contentController.validate()) {
      return;
    }
    var that = this;

    if (record.dirty && record.get('value') != null && record.get('value') !== undefined) {
      record.getProxy().extraParams = {'spread_to_channels': that.getViewModel().get('station__spread_to_channels')}
      record.save({
        success: function () {
          that.getView().fireEvent('recordSaved', record);
          record.getProxy().extraParams = {};
        }
      });
    } else {
      that.getView().fireEvent('editingCanceled', record);
    }
  },
  onCancelClick: function () {
    var contentView = this.lookupReference('contentView');
    var record = contentView.getViewModel().get('record');
    this.getView().fireEvent('editingCanceled', record);
  },
  onHelpClick: function () {
    var record = this.getViewModel().get('record');
    var nodeTypeString = yasmine.utils.NodeTypeConverter.toString(this.getViewModel().get('nodeType'));
    var nodeTypeId = nodeTypeString.toLowerCase();
    yasmine.utils.HelpUtil.helpMe(`parameter_${nodeTypeId}_${record.get('name')}`, `${nodeTypeString} ${record.get('name')}`);
  }
});

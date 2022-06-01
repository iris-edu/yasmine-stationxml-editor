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


Ext.define('yasmine.view.xml.builder.parameter.ParameterEditorController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.parameter-editor',
  id: 'parameter-editor-controller',
  requires: [
    'Ext.ux.Mediator',
    'yasmine.view.xml.builder.parameter.items.text.TextEditor',
    'yasmine.view.xml.builder.parameter.items.texthelp.TextHelpEditor',
    'yasmine.view.xml.builder.parameter.items.int.IntEditor',
    'yasmine.view.xml.builder.parameter.items.float.FloatEditor',
    'yasmine.view.xml.builder.parameter.items.latitude.LatitudeEditor',
    'yasmine.view.xml.builder.parameter.items.longitude.LongitudeEditor',
    'yasmine.view.xml.builder.parameter.items.date.DateEditor',
    'yasmine.view.xml.builder.parameter.items.site.SiteEditor',
    'yasmine.view.xml.builder.parameter.items.externalreferences.ExternalReferencesEditor',
    'yasmine.view.xml.builder.parameter.items.comments.CommentsEditor',
    'yasmine.view.xml.builder.parameter.items.operators.OperatorsEditor',
    'yasmine.view.xml.builder.parameter.items.operators.OperatorsEditorForm',
    'yasmine.view.xml.builder.parameter.items.channelequipment.ChannelEquipmentEditor',
    'yasmine.view.xml.builder.parameter.items.channeltypes.ChannelTypesEditor',
    'yasmine.view.xml.builder.parameter.items.channelresponse.ChannelResponseEditor',
    'yasmine.view.xml.builder.parameter.items.identifiers.IdentifiersEditor',
    'yasmine.view.xml.builder.parameter.items.equipments.EquipmentsEditor',
    'yasmine.view.xml.builder.parameter.items.restrictedstatus.RestrictedStatusEditor'
  ],
  init: function () {
    Ext.ux.Mediator.on('parameterEditorController-updateActionButtons', this.updateActionButtons, this);
    Ext.ux.Mediator.on('parameterEditorController-canSaveButton', this.canSaveButton, this);
  },
  createFrom: function () {
    let record = this.getViewModel().get('record');
    let content = Ext.create({xtype: record.get('class'), reference: 'contentView'});
    this.getView().add([content]);
    content.getViewModel().set('record', record);
    content.getViewModel().set('nodeType', this.getViewModel().get('nodeType'));

    let contentController = content.getController();
    if (!contentController) {
      return;
    }

    if (contentController.initData) {
      contentController.initData();
    }
  },
  updateActionButtons: function (buttons) {
    Ext.suspendLayouts();
    let container = this.lookupReference('action-buttons-container');
    container.removeAll(false);
    buttons.forEach(actionButton => {
      container.add(actionButton);
    });
    Ext.resumeLayouts(false);
  },
  canSaveButton: function (value) {
    this.getViewModel().set('canSave', value);
  },
  onSaveClick: function () {
    let contentView = this.lookupReference('contentView');
    let contentController = contentView.getController();
    if (contentController && contentController.fillRecord) {
      contentController.fillRecord();
    }
    if (contentController && contentController.validate && !contentController.validate()) {
      return;
    }
    let that = this;
    let record = contentView.getViewModel().get('record');
    if (record.dirty && record.get('value') != null && record.get('value') !== undefined) {
      record.save({
        failure: function (record, operation) {
          let message = JSON.parse(operation.getResponse().responseText).data;
          that.fireEvent('saveRecordError', message);
        },
        success: function () {
          that.getView().fireEvent('recordSaved');
        }
      });
    } else {
      that.getView().fireEvent('editingCanceled', record);
    }
  },
  onCancelClick: function () {
    let contentView = this.lookupReference('contentView');
    let record = contentView.getViewModel().get('record');
    this.getView().fireEvent('editingCanceled', record);
    Ext.ux.Mediator.fireEvent('node-editing-canceled');
  },
  onHelpClick: function () {
    let record = this.getViewModel().get('record');
    let nodeTypeString = yasmine.utils.NodeTypeConverter.toString(this.getViewModel().get('nodeType'));
    let nodeTypeId = nodeTypeString.toLowerCase();
    yasmine.utils.HelpUtil.helpMe(`parameter_${nodeTypeId}_${record.get('name')}`, `${nodeTypeString} ${record.get('name')}`);
  },
  onMaximizeClick: function () {
    if (this.getView().maximized) {
      this.getView().restore();
    } else {
      this.getView().maximize();
    }
  }
});

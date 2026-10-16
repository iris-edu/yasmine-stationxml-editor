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
* NRLv2 online support (2026): ASGSR, Alexey Emanov.
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
* 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.parameter.items.comments.CommentsEditorFormController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.comments-editor-form',
  id: 'comments-editor-form-controller', // Required for event listening
  requires: [
    'yasmine.utils.HelpUtil',
    'yasmine.utils.StationXmlHelpContext'
  ],
  parseCommentDate: function (value) {
    if (!value) return null;
    var date = Ext.Date.parse(value, yasmine.Globals.DateReadFormat, true);
    if (!date) {
      date = Ext.Date.parse(value, yasmine.Globals.DatePrintLongFormat, true);
    }
    return date;
  },
  initData: function (record, parameterId, nodeTypeId) {
    this.getViewModel().set('parameterId', parameterId);
    this.getViewModel().set('nodeTypeId', nodeTypeId);

    this.getViewModel().set('record', record);
    this.getViewModel().set('id', record.get('id'));
    this.getViewModel().set('subject', record.get('subject'));
    this.getViewModel().set('value', record.get('value'));
    this.getViewModel().set('beginEffectiveTime', this.parseCommentDate(record.get('begin_effective_time')));
    this.getViewModel().set('endEffectiveTime', this.parseCommentDate(record.get('end_effective_time')));

    let authorGrid = this.lookupReference('person-list');
    authorGrid.getViewModel().set('parameterId', this.getViewModel().get('parameterId'));
    authorGrid.getViewModel().set('nodeTypeId', this.getViewModel().get('nodeTypeId'));
    authorGrid.getViewModel().set('stationXmlPersonPath', 'Author');
    authorGrid.getViewModel().set('stationXmlParameterName', 'comments');
    authorGrid.getController().syncPersonChrome();
    authorGrid.getController().initData(record.get('authors') || []);
    this.bindHelpFields();
  },
  bindHelpFields: function () {
    var view = this.getView();
    view.stationXmlHelpRelativePath = '';
    Ext.Array.each(view.query('field'), function (field) {
      if (field.stationXmlHelpBound) {
        return;
      }
      field.stationXmlHelpBound = true;
      field.on('focus', function () {
        view.stationXmlHelpRelativePath =
          yasmine.utils.StationXmlHelpContext.relativePathForField(
            'comments',
            field
          );
      });
    });
  },
  onHelpClick: function () {
    var vm = this.getViewModel();
    yasmine.utils.HelpUtil.stationXmlHelpMe({
      nodeType: vm.get('nodeTypeId'),
      parameterName: 'comments',
      relativePath: this.getView().stationXmlHelpRelativePath
    }, 'Comment');
  },
  onSaveClick: function () {
    let record = this.getViewModel().get('record');
    let form = this.getView().down('form').getForm();
    let id = this.getViewModel().get('id');
    if (!form.isValid()) {
      return;
    }
    record.set('id', id == null || id === '' ? null : Number(id));
    record.set('subject', this.getViewModel().get('subject'));
    record.set('value', this.getViewModel().get('value'));
    var beginTime = this.getViewModel().get('beginEffectiveTime');
    var endTime = this.getViewModel().get('endEffectiveTime');
    record.set('begin_effective_time', beginTime ? Ext.Date.format(beginTime, yasmine.Globals.DateReadFormat) : null);
    record.set('end_effective_time', endTime ? Ext.Date.format(endTime, yasmine.Globals.DateReadFormat) : null);
    record.set('authors', this.lookupReference('person-list').getController().getData());

    this.fireEvent('commentUpdated', record);
    this.closeView();
  },
  onCancelClick: function () {
    this.closeView();
  }
});

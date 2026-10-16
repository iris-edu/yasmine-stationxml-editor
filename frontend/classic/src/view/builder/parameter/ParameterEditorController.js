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
* 2026-09-24, version 4.3.3-beta: ASGSR, Alexey Emanov
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
    'yasmine.view.xml.builder.parameter.items.restrictedstatus.RestrictedStatusEditor',
    'yasmine.view.xml.builder.parameter.items.dataavailability.DataAvailabilityEditor',
    'yasmine.utils.StationXmlHelpContext'
  ],
  init: function () {
    this._pendingActionButtons = [];
    this.mon(Ext.ux.Mediator, 'parameterEditorController-updateActionButtons', this.updateActionButtons, this);
    this.mon(Ext.ux.Mediator, 'parameterEditorController-canSaveButton', this.canSaveButton, this);
    this.getView().on({
      afterrender: this.flushActionButtons,
      show: this.flushActionButtons,
      scope: this
    });
  },
  createFrom: function () {
    let record = this.getViewModel().get('record');
    let win = this.getView();
    let isResponse = record.get('class') === 'yasmine-channel-response-field' ||
        record.get('attr_class') === 'yasmine-channel-response-field';
    let content = Ext.create({xtype: record.get('class'), reference: 'contentView'});
    if (isResponse) {
      win.setScrollable(false);
      if (!win.getLayout() || win.getLayout().type !== 'fit') {
        win.setLayout('fit');
      }
      if (!yasmine.utils.ResponsiveUtil.useStackLayout()) {
        win.setMinWidth(800);
        win.setMinHeight(500);
        win.setWidth(1000);
        win.setHeight(700);
      }
    } else if (content.isPanel) {
      content.flex = 1;
      content.minHeight = 0;
    }
    win.add([content]);
    this.bindHelpFields(content, record);
    if (content.getViewModel()) {
      content.getViewModel().set('record', record);
      content.getViewModel().set('nodeType', this.getViewModel().get('nodeType'));
    }

    let contentController = content.getController();
    if (!contentController) {
      return;
    }

    if (contentController.initData) {
      contentController.initData();
    }
    if (content.getViewModel && content.getViewModel() &&
        content.getViewModel().get('currentViewReference') === 'response-preview') {
      this.getViewModel().set({
        showResponseActions: true,
        showEditResponse: true,
        showSelectResponse: true,
        showRecalculateSensitivity: true,
        showImportResp: true
      });
    }
    if (isResponse) {
      this.bindResponseContentSize(win, content);
    }
  },
  bindResponseContentSize: function (win, content) {
    var repair = function () {
      if (!win || win.destroyed || !content || content.destroyed || !win.body) {
        return;
      }
      var bodyHeight = win.body.getHeight(true);
      var bodyWidth = win.body.getWidth(true);
      var contentHeight = content.getHeight();
      var contentWidth = content.getWidth();
      if (bodyHeight > 120 && contentHeight < 80) {
        content.setHeight(bodyHeight);
      }
      if (bodyWidth > 120 && contentWidth < 80) {
        content.setWidth(bodyWidth);
      }
      if (content.updateLayout) {
        content.updateLayout();
      }
    };
    win.on('show', function () {
      Ext.defer(repair, 50);
      Ext.defer(repair, 250);
    }, this);
    win.on('resize', function () {
      Ext.defer(repair, 50);
    }, this);
  },
  updateActionButtons: function (buttons) {
    this._pendingActionButtons = buttons || [];
    this.flushActionButtons();
  },
  flushActionButtons: function () {
    let container = this.lookupReference('action-buttons-container');
    let pending;
    if (!container) {
      return;
    }
    pending = this._pendingActionButtons || [];
    if (pending.length && pending.every(function (button) {
      return button && !button.destroyed && button.ownerCt === container;
    })) {
      return;
    }
    Ext.suspendLayouts();
    container.query('[actionButton]').forEach(function (item) {
      container.remove(item, pending.indexOf(item) < 0);
    });
    pending.forEach(function (button) {
      if (!button || button.destroyed) {
        return;
      }
      button.actionButton = true;
      if (button.ownerCt !== container) {
        container.add(button);
      }
    });
    this.getViewModel().set(
      'showResponseActions',
      !!(this.getViewModel().get('showEditResponse') ||
        this.getViewModel().get('showSelectResponse') ||
        this.getViewModel().get('showRecalculateSensitivity') ||
        this.getViewModel().get('showImportResp') ||
        pending.length)
    );
    Ext.resumeLayouts(true);
  },
  getContentController: function () {
    let contentView = this.lookupReference('contentView') ||
      this.getView().down('yasmine-channel-response-field') ||
      this.getView().child();
    return contentView && contentView.getController ? contentView.getController() : null;
  },
  onEditResponseClick: function () {
    let controller = this.getContentController();
    if (controller && controller.createXmlResponseEditor) {
      controller.createXmlResponseEditor();
    }
  },
  onSelectResponseClick: function () {
    let controller = this.getContentController();
    if (controller && controller.createResponseSelector) {
      controller.createResponseSelector();
    }
  },
  onRecalculateSensitivityClick: function () {
    let controller = this.getContentController();
    if (controller && controller.recalculateSensitivity) {
      controller.recalculateSensitivity();
    }
  },
  onImportRespClick: function () {
    let controller = this.getContentController();
    if (controller && controller.onImportRespClick) {
      controller.onImportRespClick();
    }
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
    if (contentController && contentController.prepareRecordForSave &&
        contentController.prepareRecordForSave() === false) {
      that.getView().fireEvent('editingCanceled', record);
      return;
    }
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
  bindHelpFields: function (content, record) {
    var me = this;
    var parameterName = record.get('name');
    var nodeType = me.getViewModel().get('nodeType');
    var setContext = function (field) {
      var relativePath =
        yasmine.utils.StationXmlHelpContext.relativePathForField(
          parameterName,
          field
        );
      me.getView().stationXmlHelpContext = {
        nodeType: nodeType,
        parameterName: parameterName,
        relativePath: relativePath
      };
    };
    var bindFields = function () {
      Ext.Array.each(content.query ? content.query('field') : [], function (field) {
        if (field.stationXmlHelpBound) {
          return;
        }
        field.stationXmlHelpBound = true;
        field.on('focus', function () {
          setContext(field);
        });
      });
    };

    me.getView().stationXmlHelpContext = {
      nodeType: nodeType,
      parameterName: parameterName
    };
    bindFields();
    content.on('afterrender', function () {
      bindFields();
      Ext.defer(bindFields, 100);
    }, me, {single: true});
    content.on('focusenter', function (component, event) {
      var field = event && event.target ?
        Ext.Component.fromElement(event.target, content.el) : null;
      if (field && field.isFormField) {
        setContext(field);
      }
    });
  },
  onHelpClick: function () {
    let record = this.getViewModel().get('record');
    let nodeTypeString = yasmine.utils.NodeTypeConverter.toString(this.getViewModel().get('nodeType'));
    yasmine.utils.HelpUtil.stationXmlHelpMe(
      this.getView().stationXmlHelpContext || {
        nodeType: this.getViewModel().get('nodeType'),
        parameterName: record.get('name')
      },
      `${nodeTypeString} ${yasmine.utils.StationXmlHelpContext.labelForRecord(record)}`
    );
  },
  onMaximizeClick: function () {
    var win = this.getView();
    if (win.maximized) {
      win.restore();
      yasmine.utils.ResponsiveUtil.fitWindow(win, {
        minWidth: 800,
        minHeight: 500,
        width: 1000,
        height: 700
      });
    } else {
      win.maximize();
    }
  }
});

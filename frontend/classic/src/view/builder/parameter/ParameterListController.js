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


Ext.define('yasmine.view.xml.builder.parameter.ParameterListController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.parameter-list',
  requires: [
    'yasmine.view.xml.builder.parameter.items.text.TextPreview',
    'yasmine.view.xml.builder.parameter.items.texthelp.TextHelpPreview',
    'yasmine.view.xml.builder.parameter.items.comments.CommentsPreview',
    'yasmine.view.xml.builder.parameter.items.date.DatePreview',
    'yasmine.view.xml.builder.parameter.items.int.IntPreview',
    'yasmine.view.xml.builder.parameter.items.latitude.LatitudePreview',
    'yasmine.view.xml.builder.parameter.items.longitude.LongitudePreview',
    'yasmine.view.xml.builder.parameter.items.operators.OperatorsPreview',
    'yasmine.view.xml.builder.parameter.items.site.SitePreview',
    'yasmine.view.xml.builder.parameter.items.float.FloatPreview',
    'yasmine.view.xml.builder.parameter.items.unrecognized.UnrecognizedPreview',
    'yasmine.view.xml.builder.parameter.items.externalreferences.ExternalReferencesPreview',
    'yasmine.view.xml.builder.parameter.items.channelequipment.ChannelEquipmentPreview',
    'yasmine.view.xml.builder.parameter.items.channeltypes.ChannelTypesPreview',
    'yasmine.view.xml.builder.parameter.items.channelresponse.ChannelResponsePreview',
    'yasmine.view.xml.builder.parameter.items.identifiers.IdentifiersPreview',
    'yasmine.view.xml.builder.parameter.items.equipments.EquipmentsPreview',
    'yasmine.view.xml.builder.parameter.items.restrictedstatus.RestrictedStatusPreview',
    'yasmine.NodeTypeEnum'
  ],
  init: function () {
    Ext.ux.Mediator.on('node-selected', this.onNodeSelected, this);
    Ext.ux.Mediator.on('node-editing-canceled', this.reloadStores, this);
  },
  onNodeSelected: function (node) {
    if (!node || node.root) {
      this.onXmlNodeDeSelected();
    } else {
      this.onXmlNodeSelected(node)
    }
  },
  onXmlNodeSelected: function (node) {
    this.getViewModel().set('nodeInstance', node);
    this.getViewModel().set('nodeType', node.nodeType);
    this.getViewModel().set('nodeId', node.id);
    this.getViewModel().set('selectedAvailableParameter', null);
    this.getViewModel().set('theRow', null);
    this.getViewModel().notify();
    this.reloadStores();
  },
  onXmlNodeDeSelected: function () {
    this.getViewModel().set('nodeInstance', null);
    this.getViewModel().set('nodeType', null);
    this.getViewModel().set('selectedAvailableParameter', null);
    this.getViewModel().set('theRow', null);
    this.getViewModel().notify();
    this.clearStores();
  },
  onRecordSaved: function () {
    this.closeForm();
    this.getViewModel().set('selectedAvailableParameter', null);
    this.reloadStores();

    Ext.ux.Mediator.fireEvent('node-updated', this.getViewModel().get('nodeInstance'));
  },
  onEditinFormgCanceled: function (record) {
    this.closeForm();
    this.onCelcelEditing(record);
    this.getViewModel().set('selectedAvailableParameter', null);
  },
  onCellKeyDown: function (cell, td, cellIndex, record, tr, rowIndex, e) {
    if (e.getKey() === e.ENTER) {
      this.onEditClick();
    }
  },
  onEditClick: function () {
    if (!this.getSelectedRecord()) {
      return;
    }

    let parameter = new yasmine.model.Parameter();
    parameter.set('id', this.getSelectedRecord().get('id'));
    parameter.load({
      scope: this,
      success: function (record) {
        this.showForm(record);
      }
    });
  },
  onCellEdit: function (editor, context) {
    if (!context.record.dirty) {
      return;
    }
    context.record.save({
      scope: this,
      success: function () {
        Ext.ux.Mediator.fireEvent('node-updated', this.getViewModel().get('nodeInstance'));
      }
    });
  },
  onCancelCellEditFinish: function (editor, context) {
    this.onCelcelEditing(context.record);
  },
  onCelcelEditing: function (record) {
    if (record.phantom) {
      var view = this.getView();
      var infoStore = view.getStore('infoStore');
      infoStore.remove(record)
      this.lookupReference('availableParamsCntr').clearValue();
    }
  },
  onCellEditValidate: function (editor, context) {
    var record = context.record;
    if (record.phantom && !context.value) {
      context.cancel = true
      return false
    }
  },
  onAddClick: function (grid, record) {
    if (!record) {
      return
    }

    var view = this.getView();
    var parameter = new yasmine.model.Parameter({
      id: null,
      'class': record.get('class'),
      attr_class: record.get('class'),
      name: record.get('name'),
      parameterId: record.get('id'),
      nodeId: this.getViewModel().get('nodeId'),
      node_id: this.getViewModel().get('nodeType'),
      node_type_id: this.getViewModel().get('nodeType') // TODO: This has to be refactored.
    });

    var infoStore = view.getStore('infoStore')
    infoStore.insert(0, parameter)
    view.setSelection(parameter)
    var curPossition = view.getSelectionModel().getCurrentPosition()
    var context = new Ext.grid.CellContext(view.getView()).setPosition(curPossition.rowIdx, view.getColumnManager().getColumns()[1]);
    this.getView().setActionableMode(true, context)
  },
  onDeleteClick: function () {
    let record = this.getSelectedRecord();
    if (record.get('required')) {
      Ext.MessageBox.alert('Error', `The "${record.get('name')}" field cannot be removed. It's a mandatory field.`);
      return;
    }
    Ext.MessageBox.confirm('Confirm', `Are you sure you want to delete '${record.get('name')}' parameter?`, function (btn) {
      if (btn === 'yes') {
        this.getSelectedRecord().erase({
          scope: this,
          success: function () {
            this.reloadStores();
            Ext.ux.Mediator.fireEvent('node-updated', this.getViewModel().get('nodeInstance'));
          }
        });
      }
    }, this);
  },
  getSelectedRecord: function () {
    return this.getView().getSelection()[0];
  },
  onBeginEdit: function (editor, context) {
    let record = context.record;
    let isComplexType = record.get('isComplexType');
    if (isComplexType) {
      this.showForm(context.record)
      return false;
    } else {
      let nodeInstance = this.getViewModel().get('nodeInstance');
      let has_children = nodeInstance.has_children;
      let commonAttrs = [
        yasmine.NodeAttrEnum.latitude,
        yasmine.NodeAttrEnum.longitude,
        yasmine.NodeAttrEnum.elevation,
        yasmine.NodeAttrEnum.start_date,
        yasmine.NodeAttrEnum.end_date
      ]
      let name = record.get('name');
      let nodeType = nodeInstance.nodeType;
      if (has_children && commonAttrs.indexOf(name) >= 0 && nodeType === yasmine.NodeTypeEnum.station) {
        this.showFormExt(context.record)
        return false
      }
    }
  },
  showForm(record) {
    this.editorWindow = Ext.create({
      xtype: 'parameter-editor',
      listeners: {
        recordSaved: {
          fn: this.onRecordSaved,
          scope: this
        },
        editingCanceled: {
          fn: this.onEditinFormgCanceled,
          scope: this
        }
      }
    });
    this.editorWindow.getViewModel().set('record', record);
    this.editorWindow.getViewModel().set('nodeType', this.getViewModel().get('nodeType'))
    try {
      this.editorWindow.getController().createFrom();
      this.editorWindow.show();
    } catch (error) {
      if (error.message.startsWith('[Ext.create] Unrecognized class name')) {
        Ext.MessageBox.alert('Error', `There is no editor for the following property: '${record.get('class')}'`);
      } else {
        throw error;
      }
    }
  },
  showFormExt(record) {
    this.editorWindow = Ext.create({
      xtype: 'parameter-editor-ext',
      listeners: {
        recordSaved: {
          fn: this.onRecordSaved,
          scope: this
        },
        editingCanceled: {
          fn: this.onEditinFormgCanceled,
          scope: this
        }
      }
    });
    this.editorWindow.getViewModel().set('record', record);
    this.editorWindow.getViewModel().set('nodeType', this.getViewModel().get('nodeType'))
    try {
      this.editorWindow.getController().createFrom();
      this.editorWindow.show();
    } catch (error) {
      if (error.message.startsWith('[Ext.create] Unrecognized class name')) {
        Ext.MessageBox.alert('Error', `There is no editor for the following property: '${record.get('class')}'`);
      } else {
        throw error;
      }
    }
  },
  closeForm() {
    this.editorWindow.close();
  },
  reloadStores() {
    this.getViewModel().getStore('infoStore').reload();
    this.getViewModel().getStore('availableParamsStore').reload();
  },
  clearStores() {
    this.lookupReference('availableParamsCntr').clearValue();
    this.getViewModel().getStore('availableParamsStore').loadData([]);
    this.getViewModel().getStore('infoStore').loadData([]);
  },
  nameRenderer: function (value, column, record) {
    let requiredSymbol = '';
    let name = value;
    if (record.get('required')) {
      requiredSymbol = '<span style="color: red">*</span>';
      name = `<b>${value}</b>`;
    }
    return `${requiredSymbol} ${name}`;
  },
  valueRenderer: function (value, column, record) {
    let preview = null;
    try {
      preview = Ext.create({xtype: `${record.get('class')}-preview`});
    } catch (error) {
      preview = Ext.create({xtype: 'unrecognized-preview'});
    }

    let result = preview.getPreview(record.get('value'), record.store.getData().items);
    if (yasmine.utils.CheckUtil.isEmpty(result)) {
      return yasmine.Globals.NotApplicable;
    }

    if (result.tooltip) {
      return `<span data-qtip="${result.tooltip}">${result.value}</span>`;
    }

    if (preview.isComplexType && preview.isComplexType()) {
      result = `<i class="fa fa-info-circle" aria-hidden="true" title="Double click to see more details"></i>  ${result}`;
    }

    return result;
  }
});

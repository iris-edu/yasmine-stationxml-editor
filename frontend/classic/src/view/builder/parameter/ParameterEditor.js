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


Ext.define('yasmine.view.xml.builder.parameter.ParameterEditor', {
  extend: 'Ext.window.Window',
  xtype: 'parameter-editor',
  requires: [
    'yasmine.view.xml.builder.parameter.ParameterEditorModel',
    'yasmine.view.xml.builder.parameter.ParameterEditorController',
    'Ext.layout.container.Table'
  ],
  controller: 'parameter-editor',
  viewModel: 'parameter-editor',
  bind: {
    title: '{title}'
  },
  bodyPadding: 4,
  modal: true,
  frame: true,
  resizable: true,
  minWidth: 800,
  minHeight: 500,
  closable: false,
  scrollable: true,
  defaultFocus: 'focusItem',
  defaultButton: 'saveButton',
  layout: 'fit',
  listeners: {
    show: function () {
      if (!this._initialSizeApplied) {
        var viewSize = Ext.getBody().getViewSize();
        this.setSize(
          Math.min(1000, Math.floor(viewSize.width * 0.85)),
          Math.min(700, Math.floor(viewSize.height * 0.8))
        );
        this._initialSizeApplied = true;
        this.center();
      }
    },
    afterlayout: function () {
      if (this.maximized) {
        return;
      }
      var viewSize = Ext.getBody().getViewSize();
      if (this.getHeight() > viewSize.height) {
        this.setHeight(viewSize.height);
      }
      if (this.getWidth() > viewSize.width) {
        this.setWidth(viewSize.width);
      }
      this.center();
    }
  },
  tools: [
    {
      type: 'help',
      handler: 'onHelpClick'
    },
    {
      type: 'maximize',
      handler: 'onMaximizeClick'
    },
    {
      type: 'close',
      handler: 'onCancelClick'
    }
  ],
  dockedItems: [
    {
      xtype: 'toolbar',
      dock: 'bottom',
      ui: 'footer',
      items: [
        {
          xtype: 'container',
          reference: 'action-buttons-container',
          defaults: {
            margin: '0 5 0 0'
          },
          items: []
        },
        '->',
        {
          text: 'Save',
          iconCls: 'x-fa fa-floppy-o',
          disabled: false,
          bind: {
            disabled: '{!canSave}'
          },
          handler: 'onSaveClick'
        },
        {
          text: 'Cancel',
          iconCls: 'x-fa fa-ban',
          handler: 'onCancelClick'
        },
      ]
    }
  ]
});

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
* 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
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
  frame: false,
  cls: 'yasmine-window yasmine-parameter-window',
  resizable: true,
  constrain: true,
  minWidth: 280,
  minHeight: 200,
  closable: false,
  scrollable: true,
  defaultFocus: 'focusItem',
  defaultButton: 'saveButton',
  layout: {
    type: 'vbox',
    align: 'stretch'
  },
  listeners: {
    show: function () {
      if (!this._initialSizeApplied) {
        yasmine.utils.ResponsiveUtil.fitWindow(this, {
          minWidth: 800,
          minHeight: 500,
          width: 1000,
          height: 700
        });
        this._initialSizeApplied = true;
      }
    },
    afterlayout: function () {
      yasmine.utils.ResponsiveUtil.clampWindow(this);
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
      xtype: 'container',
      dock: 'bottom',
      cls: 'parameter-editor-footer-wrap',
      layout: {
        type: 'vbox',
        align: 'stretch'
      },
      items: [
        {
          xtype: 'toolbar',
          ui: 'footer',
          cls: 'parameter-editor-footer parameter-editor-actions',
          reference: 'response-actions-toolbar',
          hidden: true,
          bind: {
            hidden: '{!showResponseActions}'
          },
          defaults: {
            margin: '0 5 0 0'
          },
          items: [
            {
              xtype: 'button',
              iconCls: 'x-fa fa-pencil',
              tooltip: 'Edit Response',
              hidden: true,
              bind: {
                hidden: '{!showEditResponse}',
                text: '{responseEditText}'
              },
              handler: 'onEditResponseClick'
            },
            {
              xtype: 'button',
              iconCls: 'x-fa fa-pencil',
              tooltip: 'Select a new Response',
              hidden: true,
              bind: {
                hidden: '{!showSelectResponse}',
                text: '{responseSelectText}'
              },
              handler: 'onSelectResponseClick'
            },
            {
              xtype: 'button',
              iconCls: 'x-fa fa-upload',
              tooltip: 'Import RESP',
              hidden: true,
              bind: {
                hidden: '{!showImportResp}',
                text: '{responseImportText}'
              },
              handler: 'onImportRespClick'
            },
            {
              xtype: 'button',
              iconCls: 'x-fa fa-calculator',
              tooltip: 'Recalculate Sensitivity',
              hidden: true,
              bind: {
                hidden: '{!showRecalculateSensitivity}',
                text: '{responseRecalculateText}'
              },
              handler: 'onRecalculateSensitivityClick'
            },
            {
              xtype: 'container',
              reference: 'action-buttons-container',
              cls: 'yasmine-wrap-toolbar yasmine-action-buttons',
              flex: 1,
              minWidth: 0,
              layout: {
                type: 'hbox',
                align: 'middle'
              },
              defaults: {
                margin: '0 5 0 0',
                minWidth: 0
              },
              items: []
            }
          ]
        },
        {
          xtype: 'toolbar',
          ui: 'footer',
          cls: 'parameter-editor-footer',
          defaults: {
            minWidth: 0
          },
          items: [
            '->',
            {
              text: 'Save',
              iconCls: 'x-fa fa-floppy-o',
              cls: 'yasmine-primary-action',
              reference: 'saveButton',
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
            }
          ]
        }
      ]
    }
  ]
});

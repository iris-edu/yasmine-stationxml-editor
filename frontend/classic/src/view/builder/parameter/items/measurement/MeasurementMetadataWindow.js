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
* 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.parameter.items.measurement.MeasurementMetadataWindow', {
  extend: 'Ext.window.Window',
  xtype: 'measurement-metadata-window',

  requires: [
    'yasmine.view.xml.builder.parameter.items.measurement.MeasurementMetadataWindowModel',
    'yasmine.view.xml.builder.parameter.items.measurement.MeasurementMetadataWindowController',
    'yasmine.view.xml.builder.parameter.items.float.StationXmlDoubleField'
  ],

  viewModel: 'measurement-metadata-window',
  controller: 'measurement-metadata-window',
  bind: {
    title: '{title}'
  },
  modal: true,
  frame: false,
  cls: 'yasmine-window',
  constrain: true,
  minWidth: 280,
  layout: 'fit',
  closable: false,
  defaultFocus: 'measurementMethod',

  listeners: {
    show: function () {
      yasmine.utils.ResponsiveUtil.fitWindow(this, {
        minWidth: 400,
        minHeight: 340,
        width: 480,
        height: 420
      });
    },
    afterlayout: function () {
      yasmine.utils.ResponsiveUtil.clampWindow(this);
    }
  },

  items: [{
    xtype: 'form',
    minWidth: 0,
    bodyPadding: 12,
    scrollable: 'y',
    layout: {
      type: 'vbox',
      align: 'stretch'
    },
    defaults: {
      labelWidth: 145,
      listeners: {
        focus: function (field) {
          var window = field.up('measurement-metadata-window');
          var context = window.stationXmlHelpContext || {};
          window.stationXmlHelpContext = Ext.apply({}, context, {
            relativePath: field.stationXmlRelativePath
          });
        }
      }
    },
    items: [
      {
        xtype: 'yasmine-stationxml-double-field',
        fieldLabel: 'Plus Error',
        bind: '{plusError}',
        allowBlank: true,
        stationXmlRelativePath: '@plusError',
        tooltip: 'Uncertainties are normally entered as positive values.'
      },
      {
        xtype: 'yasmine-stationxml-double-field',
        fieldLabel: 'Minus Error',
        bind: '{minusError}',
        allowBlank: true,
        stationXmlRelativePath: '@minusError',
        tooltip: 'Enter the magnitude; StationXML interprets minus error as negative.'
      },
      {
        xtype: 'textfield',
        itemId: 'measurementMethod',
        fieldLabel: 'Measurement Method',
        bind: '{measurementMethod}',
        allowBlank: true,
        stationXmlRelativePath: '@measurementMethod'
      },
      {
        xtype: 'textfield',
        fieldLabel: 'Datum',
        bind: {
          value: '{datum}',
          hidden: '{!showDatum}'
        },
        allowBlank: true,
        stationXmlRelativePath: '@datum'
      },
      {
        xtype: 'textfield',
        fieldLabel: 'Unit',
        bind: {
          value: '{unit}',
          readOnly: '{unitReadOnly}'
        },
        allowBlank: true,
        stationXmlRelativePath: '@unit'
      },
      {
        xtype: 'checkbox',
        boxLabel: 'Apply value and metadata to channels',
        bind: {
          value: '{spreadToChannels}',
          hidden: '{!spreadAllowed}'
        }
      }
    ],
    dockedItems: [{
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
          cls: 'parameter-editor-footer',
          items: [{
            text: 'Clear Metadata',
            minWidth: 0,
            handler: 'onClearClick'
          }]
        },
        {
          xtype: 'toolbar',
          ui: 'footer',
          cls: 'parameter-editor-footer',
          items: [
            '->',
            {
              text: 'Save',
              minWidth: 0,
              iconCls: 'x-fa fa-floppy-o',
              cls: 'yasmine-primary-action',
              handler: 'onSaveClick'
            },
            {
              text: 'Cancel',
              minWidth: 0,
              iconCls: 'x-fa fa-ban',
              handler: 'onCancelClick'
            }
          ]
        }
      ]
    }]
  }],

  tools: [{
    type: 'help',
    handler: function (event, target, header) {
      var window = header.up('measurement-metadata-window');
      yasmine.utils.HelpUtil.stationXmlHelpMe(
        window.stationXmlHelpContext,
        'Measurement metadata'
      );
    }
  }]
});

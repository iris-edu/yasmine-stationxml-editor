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
* 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.parameter.items.dataavailability.DataAvailabilityEditor', {
  extend: 'Ext.form.Panel',
  xtype: 'yasmine-data-availability-field',

  requires: [
    'yasmine.view.xml.builder.parameter.items.dataavailability.DataAvailabilityEditorModel',
    'yasmine.view.xml.builder.parameter.items.dataavailability.DataAvailabilityEditorController',
    'yasmine.view.xml.builder.parameter.items.float.StationXmlDoubleField'
  ],

  viewModel: 'data-availability-editor',
  controller: 'data-availability-editor',
  border: false,
  bodyPadding: 8,
  scrollable: true,
  layout: {
    type: 'vbox',
    align: 'stretch'
  },

  items: [
    {
      hidden: true,
      padding: '0 0 8 0',
      bind: {
        html: '{validationErrors}',
        hidden: '{!canShowValidationError}'
      }
    },
    {
      xtype: 'fieldset',
      reference: 'extentFieldset',
      cls: 'yasmine-data-availability-extent',
      title: 'Extent (optional)',
      checkboxToggle: true,
      collapsed: true,
      flex: 0,
      minHeight: 42,
      margin: '4 0 8 0',
      defaults: {
        xtype: 'datefield',
        anchor: '100%',
        yasmineGuiDate: 'long',
        allowBlank: false
      },
      layout: 'anchor',
      items: [
        {
          fieldLabel: 'Start (UTC)',
          itemId: 'focusItem',
          bind: '{extentStart}',
          stationXmlRelativePath: 'Extent/@start'
        },
        {
          fieldLabel: 'End (UTC)',
          bind: '{extentEnd}',
          stationXmlRelativePath: 'Extent/@end'
        }
      ]
    },
    {
      xtype: 'grid',
      reference: 'spanGrid',
      title: 'Spans',
      flex: 1,
      minHeight: 260,
      bind: {
        store: '{spanStore}',
        selection: '{selectedSpan}'
      },
      plugins: [{
        ptype: 'rowediting',
        clicksToMoveEditor: 1,
        listeners: {
          canceledit: 'onCancelSpanEditing'
        }
      }],
      columns: [
        {
          text: 'Start (UTC)',
          dataIndex: 'start',
          xtype: 'datecolumn',
          yasmineGuiDate: 'long',
          flex: 1,
          editor: {
            xtype: 'datefield',
            yasmineGuiDate: 'long',
            allowBlank: false,
            stationXmlRelativePath: 'Span/@start'
          }
        },
        {
          text: 'End (UTC)',
          dataIndex: 'end',
          xtype: 'datecolumn',
          yasmineGuiDate: 'long',
          flex: 1,
          editor: {
            xtype: 'datefield',
            yasmineGuiDate: 'long',
            allowBlank: false,
            stationXmlRelativePath: 'Span/@end'
          }
        },
        {
          text: 'Segments',
          dataIndex: 'numberSegments',
          width: 100,
          editor: {
            xtype: 'numberfield',
            allowDecimals: false,
            allowBlank: false,
            stationXmlRelativePath: 'Span/@numberSegments'
          }
        },
        {
          text: 'Maximum Time Tear (s)',
          dataIndex: 'maximumTimeTear',
          width: 175,
          editor: {
            xtype: 'yasmine-stationxml-double-field',
            allowBlank: true,
            stationXmlRelativePath: 'Span/@maximumTimeTear'
          }
        }
      ],
      tbar: [
        {
          text: 'Add Span',
          iconCls: 'x-fa fa-plus',
          handler: 'onAddSpanClick'
        },
        {
          text: 'Delete Span',
          iconCls: 'x-fa fa-minus',
          handler: 'onDeleteSpanClick',
          disabled: true,
          bind: {
            disabled: '{!selectedSpan}'
          }
        }
      ]
    }
  ]
});

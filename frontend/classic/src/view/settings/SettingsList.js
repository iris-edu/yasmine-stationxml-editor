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


Ext.define('yasmine.view.settings.SettingsList', {
  extend: 'Ext.form.Panel',
  xtype: 'settings-list',
  requires: ['yasmine.view.settings.SettingsListController', 'yasmine.view.settings.SettingsListModel', 'yasmine.XMLViewModeEnum'],
  title: 'Settings',
  frame: true,
  scrollable: true,
  controller: 'settings',
  viewModel: 'settings',
  layout: {
    type: 'hbox'
  },
  defaults: {
    margin: 10
  },
  fieldDefaults: {
    labelAlign: 'top',
    msgTarget: 'side',
    allowBlank: false,
    anchor: '100%'
  },
  items: [
    {
      xtype: 'fieldset',
      title: 'General',
      items: [
        {
          xtype: 'textfield',
          fieldLabel: 'GUI Date Format (short)',
          name: 'general__date_format_short'
        }, {
          xtype: 'textfield',
          fieldLabel: 'GUI Date Format (long)',
          name: 'general__date_format_long'
        }, {
          xtype: 'textfield',
          fieldLabel: 'XML Module',
          name: 'general__module'
        }, {
          xtype: 'textfield',
          fieldLabel: 'XML Source',
          name: 'general__source'
        }, {
          xtype: 'textfield',
          fieldLabel: 'XML URI',
          name: 'general__uri'
        }, {
          xtype: 'radiogroup',
          fieldLabel: 'XML View Mode',
          columns: 2,
          items: [
            {boxLabel: 'Tree', name: 'general__xml_view_mode', inputValue: yasmine.XMLViewModeEnum.tree},
            {boxLabel: 'Card', name: 'general__xml_view_mode', inputValue: yasmine.XMLViewModeEnum.card}
          ]
        }, {
          xtype: 'container',
          layout: {
            type: 'hbox',
            align: 'bottom',
          },
          items: [
            {
              xtype: 'textfield',
              fieldLabel: 'GATITO',
              name: 'general__user_library_source_url'
            },
            {
              xtype: 'button',
              margin: '0 0 0 10',
              iconCls: 'fa fa-refresh',
              tooltip: 'Import Generic ATomic lIbrary of Tiny Objects',
              handler: 'importUserLibraryFromUrl'
            }
          ]
        },
        {
          xtype: 'form',
          reference: 'importZipForm',
          margin: '10 0 0 0',
          listeners: {
            'actionfailed': {
              fn: function (fp, o) {
                var result = JSON.parse(o.response.responseText);
                Ext.MessageBox.show({
                  title: 'An error occurred',
                  msg: result.message,
                  buttons: Ext.MessageBox.OK,
                  icon: Ext.MessageBox['ERROR']
                });
              }, scope: this
            }
          },
          layout: {
            type: 'hbox',
            align: 'bottom',
          },
          items: [{
            xtype: 'filefield',
            emptyText: 'Import a ZIP',
            name: 'zip-path',
            allowBlank: false,
            buttonText: '',
            buttonConfig: {
              iconCls: 'fa fa-upload'
            }
          }, {
            xtype: 'button',
            margin: '0 0 0 10',
            iconCls: 'fa fa-refresh',
            tooltip: 'Import User Library',
            handler: 'importUserLibraryFromZip'
          }]
        }
      ]
    }, {
      xtype: 'fieldset',
      title: 'Network',
      items: [
        {
          xtype: 'textfield',
          fieldLabel: 'Code',
          name: 'network__code'
        },
        {
          xtype: 'numberfield',
          fieldLabel: 'Number of Stations',
          name: 'network__num_stations'
        },
        {
          xtype: 'tagfield',
          fieldLabel: 'Required Fields',
          displayField: 'id',
          valueField: 'id',
          bind: {
            store: '{networkDefaultFields}'
          },
          listeners: {
            'beforedeselect': 'onRequiredFieldDeselect'
          },
          queryMode: 'local',
          stacked: true,
          name: 'network__required_fields'
        }
      ]
    },
    {
      xtype: 'fieldset',
      title: 'Station',
      items: [
        {
          xtype: 'textfield',
          fieldLabel: 'Code',
          name: 'station__code'
        },
        {
          xtype: 'numberfield',
          fieldLabel: 'Number of Channels',
          name: 'station__num_channels'
        },
        {
          xtype: 'checkboxfield',
          boxLabel: 'Spread to Channels',
          inputValue: true,
          uncheckedValue: false,
          name: 'station__spread_to_channels'
        },
        {
          xtype: 'tagfield',
          fieldLabel: 'Required Fields',
          displayField: 'id',
          valueField: 'id',
          bind: {
            store: '{stationDefaultFields}'
          },
          listeners: {
            'beforedeselect': 'onRequiredFieldDeselect'
          },
          queryMode: 'local',
          stacked: true,
          name: 'station__required_fields'
        }
      ]
    }, {
      xtype: 'fieldset',
      title: 'Channel',
      items: [
        {
          xtype: 'textfield',
          fieldLabel: 'Code',
          name: 'channel__code'
        },
        {
          xtype: 'tagfield',
          fieldLabel: 'Required Fields',
          displayField: 'id',
          valueField: 'id',
          bind: {
            store: '{channelDefaultFields}'
          },
          listeners: {
            'beforedeselect': 'onRequiredFieldDeselect'
          },
          queryMode: 'local',
          stacked: true,
          name: 'channel__required_fields'
        }
      ]
    }],
  buttons: [{
    text: 'Save',
    iconCls: 'x-fa fa-floppy-o',
    handler: 'onSaveClick',
    // disabled: true,
    // formBind: true
  }],
  tools: [{
    type: 'help',
    handler: function () {
      yasmine.utils.HelpUtil.helpMe('settings', 'Settings')
    }
  }]
});

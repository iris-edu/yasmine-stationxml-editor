/* ****************************************************************************
* 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
*
* NRLv2 Online Response Selector
* Data from webservice (catalog + combine)
*
* NRLv2 online support (2026): ASGSR, Alexey Emanov.
*
* ****************************************************************************/

Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.nrlv2.Nrlv2ResponseSelector', {
  extend: 'Ext.tab.Panel',
  xtype: 'nrlv2-response-selector',
  reference: 'nrlv2-response-selector',
  minWidth: 0,
  requires: [
    'overrides.toolbar.Breadcrumb',
    'Ext.toolbar.Breadcrumb',
    'Ext.form.field.ComboBox',
    'Ext.grid.Panel',
    'Ext.plugin.Responsive',
    'yasmine.view.xml.builder.parameter.items.channelresponse.nrlv2.Nrlv2ResponseSelectorController',
    'yasmine.view.xml.builder.parameter.items.channelresponse.nrlv2.Nrlv2ResponseSelectorModel',
    'yasmine.view.xml.builder.parameter.items.channelresponse.preview.ResponsePreview'
  ],
  controller: 'nrlv2-response-selector',
  viewModel: 'nrlv2-response-selector',
  config: {
    responseElement: null
  },
  tabBar: {
    ui: 'sheet',
    overflowHandler: 'scroller'
  },
  cls: 'yasmine-panel-outline yasmine-response-selector',
  listeners: {
    tabchange: 'onSelectorTabChange'
  },
  items: [
    {
      bind: { title: '{instrumentTabTitle}' },
      flex: 1,
      layout: { type: 'vbox', align: 'stretch' },
      bodyPadding: 5,
      items: [
        {
          xtype: 'breadcrumb',
          showMenuIcons: true,
          showIcons: true,
          scrollable: true,
          height: 85,
          layout: 'vbox',
          useSplitButtons: true,
          componentCls: 'equipment',
          displayField: 'title',
          reference: 'dataloggerCmp',
          bind: {
            store: '{dataloggerStore}',
            selection: '{dataloggerSelection}'
          },
          defaults: { listeners: { click: 'onDataloggerClick' } },
          listeners: { change: 'onDataloggerSelectionChange' }
        },
        {
          xtype: 'container',
          reference: 'dataloggerModifierPanel',
          hidden: true,
          hideMode: 'display',
          flex: 1,
          minHeight: 0,
          layout: { type: 'vbox', align: 'stretch' },
          padding: '5 0 0 0',
          items: [
            {
              xtype: 'container',
              reference: 'dataloggerModifierForm',
              layout: { type: 'hbox', align: 'bottom' },
              plugins: 'responsive',
              responsiveConfig: {
                'width < 768 || height < 500': {
                  layout: {type: 'vbox', align: 'stretch'}
                },
                'width >= 768 && height >= 500': {
                  layout: {type: 'hbox', align: 'bottom'}
                }
              },
              padding: '0 0 5 0',
              minWidth: 0
            },
            {
              xtype: 'displayfield',
              reference: 'dataloggerConfigCount',
              bind: { value: '{dataloggerConfigCountText}' },
              padding: '0 0 5 0'
            },
            {
              xtype: 'container',
              reference: 'dataloggerConfigList',
              cls: 'nrlv2-config-list',
              flex: 1,
              minHeight: 80,
              scrollable: true,
              layout: { type: 'vbox', align: 'stretch' }
            },
            {
              xtype: 'textareafield',
              cls: 'nrlv2-config-preview',
              height: 110,
              minHeight: 80,
              grow: false,
              readOnly: true,
              scrollable: true,
              padding: '5 0 0 0',
              fieldStyle: {
                fontFamily: 'Consolas,Monaco,Lucida Console,Liberation Mono,DejaVu Sans Mono,Bitstream Vera Sans Mono,Courier New, monospace;',
                fontSize: '11px',
                whiteSpace: 'pre'
              },
              bind: { value: '{dataloggerPreviewWithConfigInfo}' }
            }
          ]
        }
      ]
    },
    {
      bind: { title: '{sensorStatus} Sensor' },
      flex: 1,
      layout: { type: 'vbox', align: 'stretch' },
      bodyPadding: 5,
      items: [
        {
          xtype: 'breadcrumb',
          showMenuIcons: true,
          showIcons: true,
          scrollable: true,
          height: 85,
          layout: 'vbox',
          useSplitButtons: true,
          componentCls: 'equipment',
          displayField: 'title',
          reference: 'sensorCmp',
          bind: {
            store: '{sensorStore}',
            selection: '{sensorSelection}'
          },
          defaults: { listeners: { click: 'onSensorClick' } },
          listeners: { change: 'onSensorSelectionChange' }
        },
        {
          xtype: 'container',
          reference: 'sensorModifierPanel',
          hidden: true,
          hideMode: 'display',
          flex: 1,
          minHeight: 0,
          layout: { type: 'vbox', align: 'stretch' },
          padding: '5 0 0 0',
          items: [
            {
              xtype: 'container',
              reference: 'sensorModifierForm',
              layout: { type: 'hbox', align: 'bottom' },
              plugins: 'responsive',
              responsiveConfig: {
                'width < 768 || height < 500': {
                  layout: {type: 'vbox', align: 'stretch'}
                },
                'width >= 768 && height >= 500': {
                  layout: {type: 'hbox', align: 'bottom'}
                }
              },
              padding: '0 0 5 0',
              minWidth: 0
            },
            {
              xtype: 'displayfield',
              reference: 'sensorConfigCount',
              bind: { value: '{sensorConfigCountText}' },
              padding: '0 0 5 0'
            },
            {
              xtype: 'container',
              reference: 'sensorConfigList',
              cls: 'nrlv2-config-list',
              flex: 1,
              minHeight: 80,
              scrollable: true,
              layout: { type: 'vbox', align: 'stretch' }
            },
            {
              xtype: 'textareafield',
              cls: 'nrlv2-config-preview',
              height: 110,
              minHeight: 80,
              grow: false,
              readOnly: true,
              scrollable: true,
              padding: '5 0 0 0',
              fieldStyle: {
                fontFamily: 'Consolas,Monaco,Lucida Console,Liberation Mono,DejaVu Sans Mono,Bitstream Vera Sans Mono,Courier New, monospace;',
                fontSize: '11px',
                whiteSpace: 'pre'
              },
              bind: { value: '{sensorPreviewWithConfigInfo}' }
            }
          ]
        }
      ]
    },
    {
      bind: {
        title: '{responseStatus} Response',
        disabled: '{!channelResponseText}'
      },
      disabled: true,
      flex: 1,
      layout: 'fit',
      bodyPadding: 5,
      items: [{ xtype: 'response-preview' }]
    }
  ]
});

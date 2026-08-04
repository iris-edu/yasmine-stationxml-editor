/* ****************************************************************************
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
  minWidth: 800,
  requires: [
    'overrides.toolbar.Breadcrumb',
    'Ext.toolbar.Breadcrumb',
    'Ext.form.field.ComboBox',
    'Ext.grid.Panel',
    'yasmine.view.xml.builder.parameter.items.channelresponse.nrlv2.Nrlv2ResponseSelectorController',
    'yasmine.view.xml.builder.parameter.items.channelresponse.nrlv2.Nrlv2ResponseSelectorModel',
    'yasmine.view.xml.builder.parameter.items.channelresponse.preview.ResponsePreview'
  ],
  controller: 'nrlv2-response-selector',
  viewModel: 'nrlv2-response-selector',
  style: 'border: solid #d0d0d0 1px;',
  listeners: {
    tabchange: 'onSelectorTabChange'
  },
  items: [
    {
      bind: { title: '{dataloggerStatus} Datalogger' },
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
          hideMode: 'visibility',
          flex: 1,
          minHeight: 120,
          layout: { type: 'vbox', align: 'stretch' },
          padding: '5 0 0 0',
          items: [
            {
              xtype: 'container',
              reference: 'dataloggerModifierForm',
              layout: { type: 'hbox', align: 'bottom' },
              padding: '0 0 5 0',
              minWidth: 400
            },
            {
              xtype: 'displayfield',
              reference: 'dataloggerConfigCount',
              bind: { value: '{dataloggerConfigCountText}' },
              padding: '0 0 5 0'
            },
            {
              xtype: 'container',
              reference: 'dataloggerConfigArea',
              flex: 1,
              minHeight: 100,
              layout: { type: 'vbox', align: 'stretch' },
              items: [
                {
                  xtype: 'container',
                  reference: 'dataloggerConfigList',
                  flex: 1,
                  scrollable: true,
                  bind: {
                    hidden: '{dataloggerFilteredCount < 1}'
                  },
                  hideMode: 'offsets',
                  layout: { type: 'vbox', align: 'stretch' }
                }
              ]
            }
          ]
        },
        {
          xtype: 'textareafield',
          flex: 1,
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
          hideMode: 'visibility',
          flex: 1,
          minHeight: 120,
          layout: { type: 'vbox', align: 'stretch' },
          padding: '5 0 0 0',
          items: [
            {
              xtype: 'container',
              reference: 'sensorModifierForm',
              layout: { type: 'hbox', align: 'bottom' },
              padding: '0 0 5 0',
              minWidth: 400
            },
            {
              xtype: 'displayfield',
              reference: 'sensorConfigCount',
              bind: { value: '{sensorConfigCountText}' },
              padding: '0 0 5 0'
            },
            {
              xtype: 'container',
              reference: 'sensorConfigArea',
              flex: 1,
              minHeight: 100,
              layout: { type: 'vbox', align: 'stretch' },
              items: [
                {
                  xtype: 'container',
                  reference: 'sensorConfigList',
                  flex: 1,
                  scrollable: true,
                  bind: {
                    hidden: '{sensorFilteredCount < 1}'
                  },
                  hideMode: 'offsets',
                  layout: { type: 'vbox', align: 'stretch' }
                }
              ]
            }
          ]
        },
        {
          xtype: 'textareafield',
          flex: 1,
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

/* 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov */
Ext.define('yasmine.view.help.stationxml.StationXmlHelp', {
  extend: 'Ext.window.Window',
  xtype: 'stationxml-help',

  requires: [
    'Ext.plugin.Responsive',
    'yasmine.view.help.stationxml.StationXmlHelpController',
    'yasmine.view.help.stationxml.StationXmlHelpModel'
  ],

  controller: 'stationxml-help',
  viewModel: 'stationxml-help',

  title: 'StationXML 1.2',
  modal: false,
  alwaysOnTop: true,
  maximizable: true,
  closeAction: 'hide',
  minWidth: 280,
  minHeight: 240,
  width: 1000,
  height: 720,
  layout: 'fit',
  cls: 'yasmine-window yasmine-help-window',
  bodyCls: 'stationxml-help-window',

  tbar: {
    cls: 'yasmine-wrap-toolbar',
    items: [{
    xtype: 'textfield',
    reference: 'searchField',
    flex: 1,
    minWidth: 80,
    emptyText: 'Search XML name, path, type or description',
    triggers: {
      clear: {
        cls: 'x-form-clear-trigger',
        handler: function (field) {
          field.setValue('');
        }
      }
    },
    listeners: {
      change: {
        fn: 'onSearchChange',
        buffer: 250
      }
    }
  }, {
    text: 'Full schema',
    iconCls: 'x-fa fa-sitemap',
    handler: 'onFullSchemaClick'
  }]
  },

  items: [{
    xtype: 'container',
    reference: 'helpLayout',
    layout: {
      type: 'hbox',
      align: 'stretch'
    },
    plugins: 'responsive',
    responsiveConfig: {
      'width < 768 || height < 500': {
        layout: {type: 'vbox', align: 'stretch'}
      },
      'width >= 768 && height >= 500': {
        layout: {type: 'hbox', align: 'stretch'}
      }
    },
    items: [{
      xtype: 'treepanel',
      reference: 'schemaTree',
      title: 'StationXML hierarchy',
      rootVisible: true,
      useArrows: true,
      scrollable: true,
      flex: 1,
      minWidth: 0,
      minHeight: 180,
      split: true,
      viewConfig: {
        enableTextSelection: true
      },
      listeners: {
        select: 'onTreeSelect'
      }
    }, {
      xtype: 'panel',
      reference: 'detailPanel',
      title: 'Schema details',
      scrollable: true,
      flex: 2,
      minWidth: 0,
      minHeight: 220,
      bodyPadding: 18,
      bodyCls: 'x-selectable stationxml-help-detail',
      listeners: {
        afterrender: 'onDetailAfterRender'
      }
    }]
  }],

  listeners: {
    show: function (window) {
      yasmine.utils.ResponsiveUtil.fitStationXmlHelpWindow(window);
    },
    afterlayout: function (window) {
      yasmine.utils.ResponsiveUtil.clampWindow(window);
    }
  },

  showContext: function (context, title) {
    this.getController().loadContext(context, title);
    this.show();
  }
});

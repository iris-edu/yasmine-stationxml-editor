/* 2026-09-27, version 4.4.0-beta: ASGSR, Alexey Emanov */
Ext.define('yasmine.view.xml.builder.map.StationMap', {
  extend: 'Ext.window.Window',
  xtype: 'station-map',
  requires: [
    'Ext.plugin.Responsive',
    'yasmine.view.xml.builder.map.StationMapController'
  ],
  controller: 'station-map',
  title: 'Map',
  modal: true,
  resizable: true,
  maximizable: true,
  constrain: true,
  cls: 'yasmine-window',
  layout: 'card',
  minWidth: 320,
  minHeight: 240,
  bodyPadding: 0,
  listeners: {
    show: function () {
      if (!this._initialSizeApplied) {
        yasmine.utils.ResponsiveUtil.fitWindow(this, {
          minWidth: 640,
          minHeight: 420,
          width: 960,
          height: 640
        });
        this._initialSizeApplied = true;
      }
    }
  },
  tbar: {
    cls: 'yasmine-map-toolbar',
    items: [
      {
        xtype: 'segmentedbutton',
        reference: 'basemapButton',
        cls: 'yasmine-map-basemap',
        items: [
          {text: 'OpenStreetMap', pressed: true, source: 'osm'},
          {text: 'OpenTopoMap', source: 'opentopomap'}
        ],
        listeners: {
          toggle: 'onBasemapToggle'
        }
      },
      '-',
      {
        xtype: 'checkbox',
        boxLabel: 'Stations',
        checked: true,
        reference: 'stationsCheck',
        cls: 'yasmine-map-stations',
        listeners: {change: 'onLayerToggle'}
      },
      {
        xtype: 'checkbox',
        boxLabel: 'Channels',
        checked: false,
        reference: 'channelsCheck',
        cls: 'yasmine-map-channels',
        listeners: {change: 'onLayerToggle'}
      },
      {
        xtype: 'checkbox',
        boxLabel: 'Station labels',
        checked: false,
        reference: 'stationLabelsCheck',
        cls: 'yasmine-map-station-labels',
        listeners: {change: 'onLayerToggle'}
      },
      {
        xtype: 'checkbox',
        boxLabel: 'Channel labels',
        checked: false,
        reference: 'channelLabelsCheck',
        cls: 'yasmine-map-channel-labels',
        listeners: {change: 'onLayerToggle'}
      },
      '->',
      {
        xtype: 'button',
        iconCls: 'x-fa fa-download',
        text: 'Download',
        tooltip: 'Download the current map as a PNG',
        reference: 'downloadButton',
        cls: 'yasmine-map-download',
        handler: 'onDownload',
        plugins: 'responsive',
        responsiveConfig: {
          'width < 768 || height < 500': {
            text: ''
          },
          'width >= 768 && height >= 500': {
            text: 'Download'
          }
        }
      },
      {xtype: 'component', cls: 'yasmine-map-row-break yasmine-map-break-basemap'},
      {xtype: 'component', cls: 'yasmine-map-row-break yasmine-map-break-stations'}
    ]
  },
  items: [
    {
      xtype: 'component',
      reference: 'mapHost',
      style: 'height:100%;width:100%;'
    },
    {
      xtype: 'component',
      reference: 'emptyMessage',
      hidden: true,
      html: '<div style="padding:24px;text-align:center;">Nothing to display. Stations and channels need numeric latitude and longitude.</div>'
    }
  ]
});

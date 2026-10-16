/* 2026-09-27, version 4.4.0-beta: ASGSR, Alexey Emanov */
Ext.define('yasmine.view.xml.builder.map.StationMapController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.station-map',

  init: function () {
    this._data = null;
    this._map = null;
    this._stationLayer = null;
    this._channelLayer = null;
    this._tileLayer = null;
    this._epochLabel = '';
    this._epochControl = null;
    this._popupMenu = null;
    var view = this.getView();
    view.on('show', this._onShow, this);
    view.on('resize', this._onResize, this);
    view.on('beforeclose', this._destroyMap, this);
  },

  loadMap: function (cfg) {
    this._mapCfg = cfg || {};
    this._channelsLoaded = false;
    this._ensureLeaflet();
    this._fetchMap(false);
  },

  _fetchMap: function (includeChannels) {
    var view = this.getView();
    var cfg = this._mapCfg || {};
    var requestId = (this._mapRequestId = (this._mapRequestId || 0) + 1);
    var params = {nodeId: cfg.nodeId || 0};
    view.setLoading(true);
    this._epochLabel = cfg.epochLabel || (cfg.epoch
      ? Ext.Date.format(cfg.epoch, yasmine.Globals.DatePrintLongFormat)
      : '');
    if (cfg.epoch) {
      params.epoch = Ext.Date.format(cfg.epoch, yasmine.Globals.DateReadFormat);
    }
    if (includeChannels) {
      params.channels = 1;
    }
    Ext.Ajax.request({
      url: '/api/xml/map/' + cfg.xmlId + '/',
      method: 'GET',
      params: params,
      scope: this,
      success: function (response) {
        if (requestId !== this._mapRequestId) {
          return;
        }
        view.setLoading(false);
        var payload = Ext.decode(response.responseText, true) || {};
        if (!payload.success) {
          Ext.Msg.alert('Map', payload.message || 'Unable to load the map');
          view.close();
          return;
        }
        this._data = payload.data || {};
        this._channelsLoaded = !!includeChannels;
        if (view.rendered) {
          this._renderMap();
        }
      },
      failure: function () {
        if (requestId !== this._mapRequestId) {
          return;
        }
        view.setLoading(false);
        Ext.Msg.alert('Map', 'Unable to load the map');
        view.close();
      }
    });
  },

  _ensureLeaflet: function (callback) {
    var assets = window.yasmineLeaflet || {js: 'leaflet.js', css: 'leaflet.css'};
    var finish = function () {
      var waiters = window._yasmineLeafletWaiters || [];
      window._yasmineLeafletWaiters = [];
      window._yasmineLeafletLoading = false;
      waiters.forEach(function (fn) {
        fn();
      });
    };
    if (typeof L !== 'undefined') {
      if (callback) {
        callback();
      }
      return;
    }
    if (!window._yasmineLeafletWaiters) {
      window._yasmineLeafletWaiters = [];
    }
    if (callback) {
      window._yasmineLeafletWaiters.push(callback);
    }
    if (window._yasmineLeafletLoading) {
      return;
    }
    window._yasmineLeafletLoading = true;
    if (assets.css && !document.getElementById('yasmine-leaflet-css')) {
      var link = document.createElement('link');
      link.id = 'yasmine-leaflet-css';
      link.rel = 'stylesheet';
      link.href = assets.css;
      document.head.appendChild(link);
    }
    var script = document.createElement('script');
    script.src = assets.js;
    script.onload = finish;
    script.onerror = function () {
      window._yasmineLeafletWaiters = [];
      window._yasmineLeafletLoading = false;
      Ext.Msg.alert('Map', 'Leaflet did not load');
    };
    document.head.appendChild(script);
  },

  onBasemapToggle: function (container, button, pressed) {
    if (!pressed || !this._map || !button.source) {
      return;
    }
    this._setBasemap(button.source);
  },

  onLayerToggle: function () {
    if (this.lookup('channelsCheck').getValue() && !this._channelsLoaded) {
      this._fetchMap(true);
      return;
    }
    this._syncLayers();
  },

  onDownload: function () {
    if (!this._map) {
      return;
    }
    var map = this._map;
    var size = map.getSize();
    var canvas = document.createElement('canvas');
    canvas.width = size.x;
    canvas.height = size.y;
    var ctx = canvas.getContext('2d');
    ctx.fillStyle = '#d7e3ea';
    ctx.fillRect(0, 0, size.x, size.y);
    var host = map.getContainer();
    var mapRect = host.getBoundingClientRect();
    var images = host.querySelectorAll('.leaflet-tile-pane img');
    var i;
    for (i = 0; i < images.length; i++) {
      var img = images[i];
      if (!img.complete || !img.naturalWidth) {
        continue;
      }
      var rect = img.getBoundingClientRect();
      try {
        ctx.drawImage(
          img,
          rect.left - mapRect.left,
          rect.top - mapRect.top,
          rect.width,
          rect.height
        );
      } catch (e) {
        // A tile that is not readable is skipped; markers are still drawn.
      }
    }
    this._drawFeatures(ctx);
    this._drawEpochBadge(ctx, size);
    this._drawAttribution(ctx, size);
    canvas.toBlob(function (blob) {
      if (!blob) {
        return;
      }
      var link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = 'yasmine-map.png';
      link.click();
      setTimeout(function () {
        URL.revokeObjectURL(link.href);
      }, 1000);
    }, 'image/png');
  },

  _onShow: function () {
    if (this._data) {
      this._renderMap();
    }
    Ext.defer(this._syncCardToolbar, 50, this);
  },

  _onResize: function () {
    this._syncCardToolbar();
    if (this._map) {
      this._map.invalidateSize();
    }
  },

  _syncCardToolbar: function () {
    var view = this.getView();
    var toolbar;
    var target;
    var height;
    var nextHeight;
    if (!view || view.destroyed) {
      return;
    }
    toolbar = view.down('toolbar');
    if (!toolbar || toolbar.destroyed || !toolbar.el) {
      return;
    }
    if (!yasmine.utils.ResponsiveUtil.useStackLayout()) {
      if (toolbar._yasmineMapWrapped) {
        toolbar._yasmineMapWrapped = false;
        toolbar.setHeight(null);
        view.updateLayout();
      }
      return;
    }
    target = toolbar.el.down('.x-box-target');
    height = target && target.dom ? target.dom.scrollHeight : 0;
    if (height <= 0) {
      return;
    }
    nextHeight = height + 8;
    if (Math.abs((toolbar.getHeight() || 0) - nextHeight) > 2) {
      toolbar._yasmineMapWrapped = true;
      toolbar.setHeight(nextHeight);
      view.updateLayout();
    }
  },

  _destroyMap: function () {
    this._hidePopupMenu();
    this._epochControl = null;
    if (this._map) {
      this._map.remove();
      this._map = null;
    }
  },

  _hidePopupMenu: function () {
    var menu = this._popupMenu;
    this._popupMenu = null;
    if (!menu || menu.destroyed) {
      return;
    }
    menu.hide();
    if (!menu.destroyed) {
      menu.destroy();
    }
  },

  _setEpochBadge: function () {
    if (!this._map) {
      return;
    }
    if (this._epochControl) {
      this._map.removeControl(this._epochControl);
      this._epochControl = null;
    }
    if (!this._epochLabel) {
      return;
    }
    var label = this._epochLabel;
    var EpochControl = L.Control.extend({
      options: {position: 'topright'},
      onAdd: function () {
        var div = L.DomUtil.create('div', 'yasmine-map-epoch');
        div.textContent = 'Epoch: ' + label;
        div.style.cssText = [
          'background:#fff',
          'border:1px solid #8aa4b5',
          'border-radius:3px',
          'padding:4px 8px',
          'margin:10px',
          'font:13px Helvetica,Arial,sans-serif',
          'color:#123b5d',
          'box-shadow:0 1px 4px rgba(0,0,0,0.25)',
          'white-space:nowrap'
        ].join(';');
        L.DomEvent.disableClickPropagation(div);
        return div;
      }
    });
    this._epochControl = new EpochControl();
    this._epochControl.addTo(this._map);
  },

  _drawEpochBadge: function (ctx, size) {
    if (!this._epochLabel) {
      return;
    }
    var text = 'Epoch: ' + this._epochLabel;
    ctx.font = '13px Helvetica, Arial, sans-serif';
    var width = Math.ceil(ctx.measureText(text).width) + 16;
    var height = 26;
    var x = size.x - width - 10;
    var y = 10;
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(x, y, width, height);
    ctx.strokeStyle = '#8aa4b5';
    ctx.lineWidth = 1;
    ctx.strokeRect(x + 0.5, y + 0.5, width - 1, height - 1);
    ctx.fillStyle = '#123b5d';
    ctx.fillText(text, x + 8, y + 17);
  },

  _renderMap: function () {
    var me = this;
    this._ensureLeaflet(function () {
      if (!me.getView() || me.getView().destroyed) {
        return;
      }
      me._paintMap();
    });
  },

  _paintMap: function () {
    var data = this._data || {};
    var stations = data.stations || [];
    var channels = data.channels || [];
    var empty = this.lookup('emptyMessage');
    var host = this.lookup('mapHost');
    var download = this.lookup('downloadButton');
    if (!stations.length && !channels.length) {
      this.getView().setActiveItem(empty);
      download.setDisabled(true);
      this._destroyMap();
      return;
    }
    this.getView().setActiveItem(host);
    download.setDisabled(false);
    if (typeof L === 'undefined') {
      Ext.Msg.alert('Map', 'Leaflet did not load');
      return;
    }
    if (!this._map) {
      var el = host.getEl().dom;
      el.style.height = '100%';
      el.style.width = '100%';
      this._map = L.map(el, {zoomControl: true, attributionControl: true});
      this._map.attributionControl.setPrefix('Leaflet');
      this._stationLayer = L.layerGroup();
      this._channelLayer = L.layerGroup();
      this._setBasemap('osm');
    }
    this._stationLayer.clearLayers();
    this._channelLayer.clearLayers();
    stations.forEach(function (row) {
      this._stationLayer.addLayer(this._marker(row, 'station'));
    }, this);
    channels.forEach(function (row) {
      this._channelLayer.addLayer(this._marker(row, 'channel'));
    }, this);
    this._syncLayers();
    this._setEpochBadge();
    this._fit(data.extent);
    var map = this._map;
    Ext.defer(function () {
      if (map) {
        map.invalidateSize();
      }
    }, 50);
  },

  _marker: function (row, kind) {
    var me = this;
    var qc = row.qc || [];
    var hasQc = qc.length > 0;
    var marker = L.marker([row.latitude, row.longitude], {
      icon: kind === 'station'
        ? this._stationIcon()
        : this._channelIcon(hasQc),
      zIndexOffset: kind === 'channel' ? 500 : 0,
      interactive: true,
      riseOnHover: true
    });
    marker._yasmineKind = kind;
    marker._yasmineLabel = row.label;
    marker._yasmineEpochs = row.epochs || [];
    marker._yasmineQc = qc;
    marker._yasmineAzimuth = row.azimuth;
    marker._yasmineDip = row.dip;
    marker.bindTooltip(this._tooltipHtml(row, kind), {
      permanent: false,
      direction: 'right',
      offset: [8, 0],
      className: 'yasmine-map-label',
      opacity: 1
    });
    marker.on('click', function (event) {
      me._onMarkerClick(event, kind);
    });
    return marker;
  },

  _tooltipHtml: function (row, kind) {
    var parts = [Ext.htmlEncode(row.label || '')];
    var qc = row.qc || [];
    if (kind === 'channel') {
      if (row.azimuth != null) {
        parts.push('Azimuth ' + Ext.htmlEncode(String(row.azimuth)) + '°');
      }
      if (row.dip != null) {
        parts.push('Dip ' + Ext.htmlEncode(String(row.dip)) + '°');
      }
    }
    if (qc.length) {
      parts.push('QC: ' + Ext.htmlEncode(qc.join(', ')));
    }
    return parts.join('<br>');
  },

  _onMarkerClick: function (event, kind) {
    var features = this._featuresNear(event.latlng, kind);
    if (!features.length) {
      return;
    }
    this._showFeatureMenu(event.originalEvent, features);
  },

  _featuresNear: function (latlng, kind) {
    var layer = kind === 'station' ? this._stationLayer : this._channelLayer;
    var map = this._map;
    var clickPoint = map.latLngToContainerPoint(latlng);
    var byLabel = {};
    var threshold = kind === 'station' ? 18 : 12;
    layer.eachLayer(function (marker) {
      var point = map.latLngToContainerPoint(marker.getLatLng());
      var dx = point.x - clickPoint.x;
      var dy = point.y - clickPoint.y;
      if ((dx * dx) + (dy * dy) > threshold * threshold) {
        return;
      }
      var label = marker._yasmineLabel;
      if (!label || byLabel[label]) {
        return;
      }
      byLabel[label] = {
        label: label,
        epochs: marker._yasmineEpochs || [],
        qc: marker._yasmineQc || [],
        azimuth: marker._yasmineAzimuth,
        dip: marker._yasmineDip
      };
    });
    return Ext.Object.getValues(byLabel).sort(function (a, b) {
      return a.label.localeCompare(b.label);
    });
  },

  _formatEpochRange: function (epoch) {
    var start = epoch && epoch.start
      ? yasmine.utils.DateUtil.formatShort(epoch.start)
      : '';
    var end = epoch && epoch.end
      ? yasmine.utils.DateUtil.formatShort(epoch.end)
      : '';
    if (start && end) {
      return start + ' – ' + end;
    }
    if (start) {
      return start;
    }
    if (end) {
      return '– ' + end;
    }
    return '(no dates)';
  },

  _showFeatureMenu: function (domEvent, features) {
    var me = this;
    var items = [];
    features.forEach(function (feature) {
      items.push({
        text: '<b>' + Ext.htmlEncode(feature.label) + '</b>',
        plain: true,
        disabled: true
      });
      var epochs = feature.epochs || [];
      if (!epochs.length) {
        items.push({
          text: '(no operating periods)',
          disabled: true
        });
      } else {
        epochs.forEach(function (epoch) {
          items.push({
            text: me._formatEpochRange(epoch),
            disabled: true
          });
        });
      }
      if (feature.azimuth != null || feature.dip != null) {
        items.push({
          text: 'Azimuth ' + (feature.azimuth != null ? feature.azimuth + '°' : '—') +
            ', Dip ' + (feature.dip != null ? feature.dip + '°' : '—'),
          disabled: true
        });
      }
      if (feature.qc && feature.qc.length) {
        items.push({
          text: 'QC: ' + feature.qc.join(', '),
          disabled: true,
          cls: 'yasmine-map-qc-flag'
        });
      }
      items.push('-');
    });
    if (items.length && items[items.length - 1] === '-') {
      items.pop();
    }
    this._hidePopupMenu();
    this._popupMenu = Ext.create('Ext.menu.Menu', {
      cls: 'yasmine-map-feature-menu',
      plain: true,
      shadow: true,
      items: items,
      listeners: {
        hide: function (menu) {
          Ext.defer(function () {
            if (menu && !menu.destroyed) {
              menu.destroy();
            }
          }, 1);
          if (me._popupMenu === menu) {
            me._popupMenu = null;
          }
        }
      }
    });
    this._popupMenu.showAt([domEvent.clientX, domEvent.clientY]);
  },

  _stationIcon: function () {
    return L.divIcon({
      className: 'yasmine-map-station-icon',
      html: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><polygon points="8,1 15,15 1,15" fill="#1a7f37" stroke="#0d4f22" stroke-width="1"/></svg>',
      iconSize: [16, 16],
      iconAnchor: [8, 8]
    });
  },

  _channelIcon: function (hasQc) {
    var fill = hasQc ? '#d97706' : '#e10600';
    var stroke = hasQc ? '#92400e' : '#7a0010';
    return L.divIcon({
      className: 'yasmine-map-channel-icon' + (hasQc ? ' yasmine-map-channel-qc' : ''),
      html: '<span style="display:block;width:8px;height:8px;margin:0;border-radius:50%;background:' +
        fill + ';border:1px solid ' + stroke + ';box-sizing:border-box;"></span>',
      iconSize: [8, 8],
      iconAnchor: [4, 4]
    });
  },

  _syncLayers: function () {
    if (!this._map) {
      return;
    }
    var showStations = this.lookup('stationsCheck').getValue();
    var showChannels = this.lookup('channelsCheck').getValue();
    var showStationLabels = this.lookup('stationLabelsCheck').getValue();
    var showChannelLabels = this.lookup('channelLabelsCheck').getValue();
    this._map.removeLayer(this._stationLayer);
    this._map.removeLayer(this._channelLayer);
    if (showStations) {
      this._map.addLayer(this._stationLayer);
    }
    if (showChannels) {
      this._map.addLayer(this._channelLayer);
    }
    this._setLabelVisibility(this._stationLayer, showStationLabels && showStations);
    this._setLabelVisibility(this._channelLayer, showChannelLabels && showChannels);
  },

  _setLabelVisibility: function (group, visible) {
    group.eachLayer(function (marker) {
      var tip = marker.getTooltip();
      if (!tip) {
        return;
      }
      tip.options.permanent = !!visible;
      if (visible) {
        marker.openTooltip();
      } else {
        marker.closeTooltip();
      }
    });
  },

  _setBasemap: function (source) {
    if (!this._map) {
      return;
    }
    if (this._tileLayer) {
      this._map.removeLayer(this._tileLayer);
    }
    var attribution = source === 'opentopomap'
      ? 'Map data: © OpenStreetMap contributors, SRTM | Style: © OpenTopoMap (CC-BY-SA)'
      : '© OpenStreetMap contributors';
    this._tileLayer = L.tileLayer('/api/map/tiles/' + source + '/{z}/{x}/{y}', {
      attribution: attribution,
      maxZoom: 17
    });
    this._tileLayer.addTo(this._map);
  },

  _fit: function (extent) {
    if (!extent) {
      this._map.setView([0, 0], 2);
      return;
    }
    var southWest = L.latLng(extent.south, extent.west, true);
    var northEast = L.latLng(extent.north, extent.east, true);
    this._map.fitBounds(L.latLngBounds(southWest, northEast));
  },

  _drawFeatures: function (ctx) {
    var showStations = this.lookup('stationsCheck').getValue();
    var showChannels = this.lookup('channelsCheck').getValue();
    var showStationLabels = this.lookup('stationLabelsCheck').getValue();
    var showChannelLabels = this.lookup('channelLabelsCheck').getValue();
    if (showStations) {
      this._drawGroup(ctx, this._data.stations || [], 'station', showStationLabels);
    }
    if (showChannels) {
      this._drawGroup(ctx, this._data.channels || [], 'channel', showChannelLabels);
    }
  },

  _drawOutlinedLabel: function (ctx, text, x, y) {
    ctx.font = '12px Helvetica, Arial, sans-serif';
    ctx.lineJoin = 'round';
    ctx.miterLimit = 2;
    ctx.lineWidth = 4;
    ctx.strokeStyle = '#ffffff';
    ctx.strokeText(text, x, y);
    ctx.fillStyle = '#123b5d';
    ctx.fillText(text, x, y);
  },

  _drawGroup: function (ctx, rows, kind, showLabels) {
    var map = this._map;
    var drawLabel = this._drawOutlinedLabel.bind(this);
    rows.forEach(function (row) {
      var point = map.latLngToContainerPoint([row.latitude, row.longitude]);
      ctx.beginPath();
      if (kind === 'station') {
        ctx.moveTo(point.x, point.y - 8);
        ctx.lineTo(point.x + 7, point.y + 7);
        ctx.lineTo(point.x - 7, point.y + 7);
        ctx.closePath();
        ctx.fillStyle = '#1a7f37';
        ctx.strokeStyle = '#0d4f22';
        ctx.lineWidth = 1;
        ctx.fill();
        ctx.stroke();
      } else {
        ctx.arc(point.x, point.y, 4, 0, Math.PI * 2);
        ctx.fillStyle = '#e10600';
        ctx.fill();
        ctx.lineWidth = 1;
        ctx.strokeStyle = '#7a0010';
        ctx.stroke();
      }
      if (showLabels && row.label) {
        drawLabel(ctx, row.label, point.x + 10, point.y - 4);
      }
    });
  },

  _drawAttribution: function (ctx, size) {
    var text = this._tileLayer && this._tileLayer.options.attribution
      ? this._tileLayer.options.attribution.replace(/<[^>]+>/g, '')
      : '';
    if (!text) {
      return;
    }
    ctx.fillStyle = 'rgba(255,255,255,0.85)';
    ctx.fillRect(0, size.y - 22, size.x, 22);
    ctx.fillStyle = '#333';
    ctx.font = '11px Helvetica, Arial, sans-serif';
    ctx.fillText(text, 8, size.y - 7);
  }
});

/* ****************************************************************************
*
* NRLv2 Response Selector Controller - Same logic as NRL, data from webservice
*
* NRLv2 online support (2026): ASGSR, Alexey Emanov.
*
* ****************************************************************************/

Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.nrlv2.Nrlv2ResponseSelectorController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.nrlv2-response-selector',
  requires: ['yasmine.utils.ResponseRecalculateUtil'],

  initViewModel: function () {
    let dataloggerStore = this.getStore('dataloggerStore');
    let sensorStore = this.getStore('sensorStore');
    dataloggerStore.on('load', this.onStoreLoad, this);
    dataloggerStore.on('beforeload', this.onDataloggerStoreBeforeLoad, this);
    sensorStore.on('load', this.onStoreLoad, this);
    sensorStore.on('beforeload', this.onSensorStoreBeforeLoad, this);
    dataloggerStore.getRoot().expand();
    sensorStore.getRoot().expand();
    this.syncActiveSelectorTab();
  },

  syncActiveSelectorTab: function () {
    let tabPanel = this.getView();
    let activeTab = tabPanel.getActiveTab();
    if (activeTab) {
      this.getViewModel().set('activeSelectorTab', tabPanel.items.indexOf(activeTab));
    }
  },

  onSelectorTabChange: function (tabPanel, newTab) {
    this.getViewModel().set('activeSelectorTab', tabPanel.items.indexOf(newTab));
    yasmine.utils.ResponseRecalculateUtil.updateWizardActionButtons(this.getViewModel());
    yasmine.utils.ResponseRecalculateUtil.updateParameterEditorActionButtons(this.getViewModel());
  },

  onSensorStoreBeforeLoad: function (store, operation) {
    let node = operation.node;
    let nodeId = node ? node.getId() : (operation.id !== undefined ? operation.id : null);
    if ((nodeId === undefined || nodeId === null) && operation.getParams) {
      let p = operation.getParams();
      nodeId = p && p.node;
    }
    if (nodeId !== undefined && nodeId !== null) {
      let parts = String(nodeId).split('/');
      if (parts.length === 2) {
        return false;
      }
    }
  },

  onDataloggerStoreBeforeLoad: function (store, operation) {
    let node = operation.node;
    let nodeId = node ? node.getId() : (operation.id !== undefined ? operation.id : null);
    if ((nodeId === undefined || nodeId === null) && operation.getParams) {
      let p = operation.getParams();
      nodeId = p && p.node;
    }
    if (nodeId !== undefined && nodeId !== null) {
      let parts = String(nodeId).split('/');
      if (parts.length === 2) {
        return false;
      }
    }
  },

  onStoreLoad: function (store, records, successful, deferredCount) {
    let me = this;
    deferredCount = deferredCount || 0;
    let root = store.getRoot();
    let breadcrumb = store === this.getStore('dataloggerStore')
      ? this.lookupReference('dataloggerCmp')
      : this.lookupReference('sensorCmp');
    if (!breadcrumb && root && root.hasChildNodes() && deferredCount < 5) {
      Ext.defer(function () { me.onStoreLoad(store, records, successful, deferredCount + 1); }, 100);
      return;
    }
    if (!breadcrumb) return;
    let sel = breadcrumb.getSelection();
    if (root && root.hasChildNodes && root.hasChildNodes() && !sel) {
      breadcrumb.setSelection(root);
    }
    if (successful && records && records.length === 0) {
      // TreeStore passes (store, records, successful, operation, node) - use node from 5th arg or operation.node
      let loadedNode = (arguments.length > 4 && arguments[4]) ? arguments[4] : null;
      if (!loadedNode) {
        let op = arguments[3];
        loadedNode = (op && typeof op === 'object' && op.node) ? op.node : null;
      }
      if (loadedNode && !loadedNode.hasChildNodes()) {
        let path = loadedNode.getId ? String(loadedNode.getId() || '') : '';
        let parts = path ? path.split('/') : [];
        let isManufacturer = parts.length === 1 && path !== '0' && path !== 'root';
        let msg = store === this.getStore('dataloggerStore')
          ? 'Manufacturer has no models'
          : 'Manufacturer has no sensors';
        if (isManufacturer) {
          loadedNode.appendChild({
            text: msg,
            id: path + '/_empty',
            leaf: true,
            _emptyPlaceholder: true
          });
          Ext.defer(function () {
            me.refreshBreadcrumbArrow(breadcrumb, loadedNode);
          }, 100);
        }
      }
    }
  },

  init: function () {
    let me = this;
    this.getView().on('boxready', function () {
      me.setupBreadcrumbLoadOnSelect(me.lookupReference('dataloggerCmp'), me.getStore('dataloggerStore'));
      me.setupBreadcrumbLoadOnSelect(me.lookupReference('sensorCmp'), me.getStore('sensorStore'));
      me.setupDataloggerModifierPanel();
      me.setupSensorModifierPanel();
    });
  },

  setupDataloggerModifierPanel: function () {
    let me = this;
    let breadcrumb = this.lookupReference('dataloggerCmp');
    if (!breadcrumb) return;
    me._dataloggerConfigLoadingPath = null;
    breadcrumb.on('selectionchange', function (cmp, node) {
      if (!node) {
        me._dataloggerConfigLoadingPath = null;
        me.clearDataloggerModifierPanel();
        return;
      }
      let path = node.getId && node.getId();
      if (!path || path === '0' || path === 'root') {
        me._dataloggerConfigLoadingPath = null;
        me.clearDataloggerModifierPanel();
        return;
      }
      let parts = String(path).split('/');
      if (parts.length === 2 && !node.isLeaf()) {
        if (me._dataloggerConfigLoadingPath === path) {
          return;
        }
        me._dataloggerConfigLoadingPath = path;
        me.loadDataloggerConfigurations(parts[0], parts[1]);
      } else {
        me._dataloggerConfigLoadingPath = null;
        me.clearDataloggerModifierPanel();
      }
    });
  },

  clearDataloggerModifierPanel: function () {
    let vm = this.getViewModel();
    vm.set('dataloggerModelPath', null);
    vm.set('dataloggerConfigurations', null);
    vm.set('dataloggerParameterNames', []);
    vm.set('dataloggerParameterOptions', {});
    vm.set('dataloggerModifierValues', {});
    vm.set('dataloggerSelectedConfig', null);
    vm.set('dataloggerSelectedConfigInfo', '');
    let panel = this.lookupReference('dataloggerModifierPanel');
    if (panel) panel.setHidden(true);
  },

  loadDataloggerConfigurations: function (manufacturer, model) {
    let me = this;
    Ext.Ajax.request({
      url: '/api/nrlv2/datalogger/configurations/',
      method: 'GET',
      params: { manufacturer: manufacturer, model: model },
      timeout: 35000,
      success: function (resp) {
        me._dataloggerConfigLoadingPath = null;
        let result = JSON.parse(resp.responseText);
        let data = result && result.data;
        if (data) {
          me.updateModifierPanel(data);
        } else {
          me.clearDataloggerModifierPanel();
        }
      },
      failure: function () {
        me._dataloggerConfigLoadingPath = null;
        me.clearDataloggerModifierPanel();
      }
    });
  },

  updateModifierPanel: function (data) {
    let vm = this.getViewModel();
    let me = this;
    let configs = data.configurations || [];
    let paramNames = data.parameterNames || [];
    let paramOptions = data.parameterOptions || {};

    vm.set('dataloggerModelPath', data.modelPath || null);
    vm.set('dataloggerConfigurations', configs);
    vm.set('dataloggerParameterNames', paramNames);
    vm.set('dataloggerParameterOptions', paramOptions);

    let modifierValues = {};
    paramNames.forEach(function (p) {
      modifierValues[p] = '*';
    });
    vm.set('dataloggerModifierValues', modifierValues);

    Ext.defer(function () {
      let form = me.lookupReference('dataloggerModifierForm');
      let panel = me.lookupReference('dataloggerModifierPanel');
      if (!form || !panel) return;

      Ext.suspendLayouts();
      form.removeAll(true);
      paramNames.forEach(function (pname) {
        let opts = paramOptions[pname] || ['*'];
        form.add({
          xtype: 'combobox',
          itemId: 'modifier_' + pname.replace(/[^a-zA-Z0-9_]/g, '_'),
          fieldLabel: pname,
          labelAlign: 'top',
          queryMode: 'local',
          displayField: 'value',
          valueField: 'value',
          forceSelection: false,
          anyMatch: true,
          editable: false,
          width: 240,
          minWidth: 240,
          listConfig: {
            minWidth: 280
          },
          store: Ext.create('Ext.data.Store', {
            fields: ['value'],
            data: opts.map(function (v) { return { value: v }; })
          }),
          value: '*',
          margin: '0 10 0 0',
          listeners: {
            change: function (cb, newVal) {
              let vals = Ext.Object.merge({}, vm.get('dataloggerModifierValues') || {});
              vals[pname] = newVal;
              vm.set('dataloggerModifierValues', vals);
              // Manual combo change invalidates previously selected concrete configuration.
              me.clearDataloggerSelectedConfigState();
              me.refreshDataloggerModifierOptions();
              me.refreshDataloggerConfigStore();
            }
          }
        });
      });
      panel.setHidden(false);
      Ext.resumeLayouts(true);
      Ext.defer(function () {
        me.refreshDataloggerModifierOptions();
        me.refreshDataloggerConfigStore();
      }, 1);

      Ext.defer(function () {
        me.syncDataloggerModifierCombos(me.getViewModel().get('dataloggerModifierValues'));
      }, 100);
    }, 10);
  },

  getFilteredConfigsByModifierValues: function (configurations, modifierValues, paramNames) {
    let configs = configurations || [];
    let vals = modifierValues || {};
    let names = paramNames || [];
    if (!names.length) return configs;
    return configs.filter(function (c) {
      let params = c.parameters || {};
      for (let i = 0; i < names.length; i++) {
        let pname = names[i];
        let sel = vals[pname];
        if (sel && sel !== '*') {
          if (String(params[pname] || '').trim() !== String(sel).trim()) {
            return false;
          }
        }
      }
      return true;
    });
  },

  refreshDataloggerConfigStore: function () {
    let vm = this.getViewModel();
    let configs = this.getFilteredConfigsByModifierValues(
      vm.get('dataloggerConfigurations'),
      vm.get('dataloggerModifierValues'),
      vm.get('dataloggerParameterNames')
    );
    let selected = vm.get('dataloggerSelectedConfig');
    let list = this.lookupReference('dataloggerConfigList');
    if (!list) return;

    // Clear selection if selected config is no longer in the filtered list (combo values changed).
    if (selected && !configs.some(function (c) { return c.instconfig === selected.instconfig; })) {
      this.clearDataloggerSelectedConfigState();
      selected = null;
    }

    list.suspendLayouts();
    list.removeAll(true);
    if (configs.length > 0) {
      let me = this;
      configs.forEach(function (cfg) {
        let text = cfg.description || cfg.instconfig || '';
        let isSelected = selected && selected.instconfig === cfg.instconfig;
        list.add({
          xtype: 'button',
          text: text,
          textAlign: 'left',
          margin: '0 0 4 0',
          cls: isSelected ? 'x-btn-default-small x-btn-pressed' : '',
          style: 'white-space: normal;',
          handler: function () {
            me.selectDataloggerConfig(cfg);
          }
        });
      });
    }
    list.resumeLayouts(true);
  },

  refreshDataloggerModifierOptions: function () {
    let vm = this.getViewModel();
    let form = this.lookupReference('dataloggerModifierForm');
    if (!form) return;
    let paramNames = vm.get('dataloggerParameterNames') || [];
    let allConfigs = vm.get('dataloggerConfigurations') || [];
    let allOptions = vm.get('dataloggerParameterOptions') || {};
    let modifierValues = Ext.Object.merge({}, vm.get('dataloggerModifierValues') || {});
    let changed = false;

    paramNames.forEach(function (pname) {
      let itemId = 'modifier_' + pname.replace(/[^a-zA-Z0-9_]/g, '_');
      let item = form.down('#' + itemId);
      if (!item) return;

      let allowedMap = {};
      allConfigs.forEach(function (cfg) {
        let params = cfg.parameters || {};
        let matchesOthers = true;
        paramNames.forEach(function (other) {
          if (other === pname || !matchesOthers) return;
          let sel = modifierValues[other];
          if (sel && sel !== '*') {
            if (String(params[other] || '').trim() !== String(sel).trim()) {
              matchesOthers = false;
            }
          }
        });
        if (matchesOthers) {
          let v = params[pname];
          if (v !== undefined && v !== null && String(v).trim()) {
            allowedMap[String(v).trim()] = true;
          }
        }
      });

      let baseOrdered = (allOptions[pname] || [])
        .map(function (v) { return String(v).trim(); })
        .filter(function (v) { return v && v !== '*'; });
      let allowedOrdered = baseOrdered.filter(function (v) { return !!allowedMap[v]; });
      Ext.Object.each(allowedMap, function (v) {
        if (allowedOrdered.indexOf(v) < 0) {
          allowedOrdered.push(v);
        }
      });
      let newOptions = ['*'].concat(allowedOrdered);

      let comboStore = item.getStore && item.getStore();
      if (comboStore) {
        comboStore.loadData(newOptions.map(function (v) { return { value: v }; }));
      }

      let current = modifierValues[pname] !== undefined ? String(modifierValues[pname]).trim() : '*';
      if (newOptions.indexOf(current) < 0) {
        current = '*';
        modifierValues[pname] = '*';
        changed = true;
      }

      item.suspendEvents(false);
      item.setValue(current);
      if (!item.getRawValue || !item.getRawValue()) {
        item.setRawValue(current);
      }
      item.resumeEvents();
    });

    if (changed) {
      vm.set('dataloggerModifierValues', modifierValues);
    }
  },

  clearDataloggerSelectedConfigState: function () {
    let vm = this.getViewModel();
    if (!vm.get('dataloggerSelectedConfig') && !vm.get('dataloggerInstconfig')) {
      return;
    }
    vm.set('dataloggerSelectedConfig', null);
    vm.set('dataloggerSelectedConfigInfo', '');
    vm.set('dataloggerInstconfig', null);
    vm.set('dataloggerSource', null);
    vm.set('dataloggerPreview', null);
    vm.set('channelResponseText', null);
    vm.set('channelResponseImageUrl', null);
    vm.set('channelResponseCsvUrl', null);
    vm.set('channelResponsePlotMessage', null);
    Ext.ux.Mediator.fireEvent('parameterEditorController-canSaveButton', false);
  },

  selectDataloggerConfig: function (config) {
    let vm = this.getViewModel();
    vm.set('dataloggerSelectedConfig', config);
    vm.set('dataloggerInstconfig', config.instconfig);
    vm.set('dataloggerSource', config.source);
    let params = config.parameters || {};
    let modifierValues = {};
    vm.get('dataloggerParameterNames').forEach(function (p) {
      modifierValues[p] = params[p] !== undefined && params[p] !== null ? String(params[p]) : '*';
    });
    vm.set('dataloggerModifierValues', modifierValues);
    vm.set('dataloggerSelectedConfigInfo', this.buildDataloggerSelectedConfigInfo(config));
    this.refreshDataloggerModifierOptions();
    this.syncDataloggerModifierCombos(modifierValues);
    this.loadPreviewResponse('datalogger', config.instconfig, config.source);
    this.refreshDataloggerConfigStore();
  },

  buildDataloggerSelectedConfigInfo: function (config) {
    if (!config) return '';
    let lines = [];
    lines.push('Selected datalogger configuration:');
    lines.push(config.description || config.instconfig || '');
    let params = config.parameters || {};
    let pkeys = Object.keys(params);
    if (pkeys.length) {
      lines.push('Parameters: ' + pkeys.map(function (k) {
        return k + ' ' + String(params[k]);
      }).join('; '));
    }
    return lines.join('\n');
  },

  syncDataloggerModifierCombos: function (modifierValues) {
    let form = this.lookupReference('dataloggerModifierForm');
    if (!form || !modifierValues) return;
    let paramNames = this.getViewModel().get('dataloggerParameterNames') || [];
    paramNames.forEach(function (pname) {
      let itemId = 'modifier_' + pname.replace(/[^a-zA-Z0-9_]/g, '_');
      let item = form.down('#' + itemId);
      if (item && modifierValues[pname] !== undefined) {
        let targetValue = String(modifierValues[pname]).trim();
        let comboStore = item.getStore && item.getStore();
        if (comboStore) {
          let idx = comboStore.findExact('value', targetValue);
          if (idx < 0) {
            comboStore.add({ value: targetValue });
          }
        }
        item.suspendEvents(false);
        item.setValue(targetValue);
        // Fallback for Ext edge-cases where value exists but display is not resolved yet.
        if (!item.getRawValue || !item.getRawValue()) {
          item.setRawValue(targetValue);
        }
        item.resumeEvents();
      }
    });
  },

  onDataloggerConfigSelect: function (grid, record) {
    let rec = record || (grid && grid.getSelection && grid.getSelection()[0]);
    if (rec) {
      this.selectDataloggerConfig(rec.getData ? rec.getData() : rec);
    }
  },

  setupSensorModifierPanel: function () {
    let me = this;
    let breadcrumb = this.lookupReference('sensorCmp');
    if (!breadcrumb) return;
    me._sensorConfigLoadingPath = null;
    breadcrumb.on('selectionchange', function (cmp, node) {
      if (!node) {
        me._sensorConfigLoadingPath = null;
        me.clearSensorModifierPanel();
        return;
      }
      let path = node.getId && node.getId();
      if (!path || path === '0' || path === 'root') {
        me._sensorConfigLoadingPath = null;
        me.clearSensorModifierPanel();
        return;
      }
      let parts = String(path).split('/');
      if (parts.length === 2 && !node.isLeaf()) {
        if (me._sensorConfigLoadingPath === path) {
          return;
        }
        me._sensorConfigLoadingPath = path;
        me.loadSensorConfigurations(parts[0], parts[1]);
      } else {
        me._sensorConfigLoadingPath = null;
        me.clearSensorModifierPanel();
      }
    });
  },

  clearSensorModifierPanel: function () {
    let vm = this.getViewModel();
    vm.set('sensorModelPath', null);
    vm.set('sensorConfigurations', null);
    vm.set('sensorParameterNames', []);
    vm.set('sensorParameterOptions', {});
    vm.set('sensorModifierValues', {});
    vm.set('sensorSelectedConfig', null);
    vm.set('sensorSelectedConfigInfo', '');
    let panel = this.lookupReference('sensorModifierPanel');
    if (panel) panel.setHidden(true);
  },

  loadSensorConfigurations: function (manufacturer, model) {
    let me = this;
    Ext.Ajax.request({
      url: '/api/nrlv2/sensor/configurations/',
      method: 'GET',
      params: { manufacturer: manufacturer, model: model },
      timeout: 35000,
      success: function (resp) {
        me._sensorConfigLoadingPath = null;
        let result = JSON.parse(resp.responseText);
        let data = result && result.data;
        if (data) {
          me.updateSensorModifierPanel(data);
        } else {
          me.clearSensorModifierPanel();
        }
      },
      failure: function () {
        me._sensorConfigLoadingPath = null;
        me.clearSensorModifierPanel();
      }
    });
  },

  updateSensorModifierPanel: function (data) {
    let vm = this.getViewModel();
    let me = this;
    let configs = data.configurations || [];
    let paramNames = data.parameterNames || [];
    let paramOptions = data.parameterOptions || {};

    vm.set('sensorModelPath', data.modelPath || null);
    vm.set('sensorConfigurations', configs);
    vm.set('sensorParameterNames', paramNames);
    vm.set('sensorParameterOptions', paramOptions);

    let modifierValues = {};
    paramNames.forEach(function (p) {
      modifierValues[p] = '*';
    });
    vm.set('sensorModifierValues', modifierValues);

    Ext.defer(function () {
      let form = me.lookupReference('sensorModifierForm');
      let panel = me.lookupReference('sensorModifierPanel');
      if (!form || !panel) return;

      Ext.suspendLayouts();
      form.removeAll(true);
      paramNames.forEach(function (pname) {
        let opts = paramOptions[pname] || ['*'];
        form.add({
          xtype: 'combobox',
          itemId: 'sensor_modifier_' + pname.replace(/[^a-zA-Z0-9_]/g, '_'),
          fieldLabel: pname,
          labelAlign: 'top',
          queryMode: 'local',
          displayField: 'value',
          valueField: 'value',
          forceSelection: false,
          anyMatch: true,
          editable: false,
          width: 240,
          minWidth: 240,
          listConfig: {
            minWidth: 280
          },
          store: Ext.create('Ext.data.Store', {
            fields: ['value'],
            data: opts.map(function (v) { return { value: v }; })
          }),
          value: '*',
          margin: '0 10 0 0',
          listeners: {
            change: function (cb, newVal) {
              let vals = Ext.Object.merge({}, vm.get('sensorModifierValues') || {});
              vals[pname] = newVal;
              vm.set('sensorModifierValues', vals);
              me.clearSensorSelectedConfigState();
              me.refreshSensorModifierOptions();
              me.refreshSensorConfigStore();
            }
          }
        });
      });
      panel.setHidden(false);
      Ext.resumeLayouts(true);
      Ext.defer(function () {
        me.refreshSensorModifierOptions();
        me.refreshSensorConfigStore();
      }, 1);

      Ext.defer(function () {
        me.syncSensorModifierCombos(me.getViewModel().get('sensorModifierValues'));
      }, 100);
    }, 10);
  },

  refreshSensorConfigStore: function () {
    let vm = this.getViewModel();
    let configs = this.getFilteredConfigsByModifierValues(
      vm.get('sensorConfigurations'),
      vm.get('sensorModifierValues'),
      vm.get('sensorParameterNames')
    );
    let selected = vm.get('sensorSelectedConfig');
    let list = this.lookupReference('sensorConfigList');
    if (!list) return;

    if (selected && !configs.some(function (c) { return c.instconfig === selected.instconfig; })) {
      this.clearSensorSelectedConfigState();
      selected = null;
    }

    list.suspendLayouts();
    list.removeAll(true);
    if (configs.length > 0) {
      let me = this;
      configs.forEach(function (cfg) {
        let text = cfg.description || cfg.instconfig || '';
        let isSelected = selected && selected.instconfig === cfg.instconfig;
        list.add({
          xtype: 'button',
          text: text,
          textAlign: 'left',
          margin: '0 0 4 0',
          cls: isSelected ? 'x-btn-default-small x-btn-pressed' : '',
          style: 'white-space: normal;',
          handler: function () {
            me.selectSensorConfig(cfg);
          }
        });
      });
    }
    list.resumeLayouts(true);
  },

  refreshSensorModifierOptions: function () {
    let vm = this.getViewModel();
    let form = this.lookupReference('sensorModifierForm');
    if (!form) return;
    let paramNames = vm.get('sensorParameterNames') || [];
    let allConfigs = vm.get('sensorConfigurations') || [];
    let allOptions = vm.get('sensorParameterOptions') || {};
    let modifierValues = Ext.Object.merge({}, vm.get('sensorModifierValues') || {});
    let changed = false;

    paramNames.forEach(function (pname) {
      let itemId = 'sensor_modifier_' + pname.replace(/[^a-zA-Z0-9_]/g, '_');
      let item = form.down('#' + itemId);
      if (!item) return;

      let allowedMap = {};
      allConfigs.forEach(function (cfg) {
        let params = cfg.parameters || {};
        let matchesOthers = true;
        paramNames.forEach(function (other) {
          if (other === pname || !matchesOthers) return;
          let sel = modifierValues[other];
          if (sel && sel !== '*') {
            if (String(params[other] || '').trim() !== String(sel).trim()) {
              matchesOthers = false;
            }
          }
        });
        if (matchesOthers) {
          let v = params[pname];
          if (v !== undefined && v !== null && String(v).trim()) {
            allowedMap[String(v).trim()] = true;
          }
        }
      });

      let baseOrdered = (allOptions[pname] || [])
        .map(function (v) { return String(v).trim(); })
        .filter(function (v) { return v && v !== '*'; });
      let allowedOrdered = baseOrdered.filter(function (v) { return !!allowedMap[v]; });
      Ext.Object.each(allowedMap, function (v) {
        if (allowedOrdered.indexOf(v) < 0) {
          allowedOrdered.push(v);
        }
      });
      let newOptions = ['*'].concat(allowedOrdered);

      let comboStore = item.getStore && item.getStore();
      if (comboStore) {
        comboStore.loadData(newOptions.map(function (v) { return { value: v }; }));
      }

      let current = modifierValues[pname] !== undefined ? String(modifierValues[pname]).trim() : '*';
      if (newOptions.indexOf(current) < 0) {
        current = '*';
        modifierValues[pname] = '*';
        changed = true;
      }

      item.suspendEvents(false);
      item.setValue(current);
      if (!item.getRawValue || !item.getRawValue()) {
        item.setRawValue(current);
      }
      item.resumeEvents();
    });

    if (changed) {
      vm.set('sensorModifierValues', modifierValues);
    }
  },

  clearSensorSelectedConfigState: function () {
    let vm = this.getViewModel();
    if (!vm.get('sensorSelectedConfig') && !vm.get('sensorInstconfig')) {
      return;
    }
    vm.set('sensorSelectedConfig', null);
    vm.set('sensorSelectedConfigInfo', '');
    vm.set('sensorInstconfig', null);
    vm.set('sensorSource', null);
    vm.set('sensorPreview', null);
    vm.set('channelResponseText', null);
    vm.set('channelResponseImageUrl', null);
    vm.set('channelResponseCsvUrl', null);
    vm.set('channelResponsePlotMessage', null);
    Ext.ux.Mediator.fireEvent('parameterEditorController-canSaveButton', false);
  },

  selectSensorConfig: function (config) {
    let vm = this.getViewModel();
    vm.set('sensorSelectedConfig', config);
    vm.set('sensorInstconfig', config.instconfig);
    vm.set('sensorSource', config.source);
    let params = config.parameters || {};
    let modifierValues = {};
    vm.get('sensorParameterNames').forEach(function (p) {
      modifierValues[p] = params[p] !== undefined && params[p] !== null ? String(params[p]) : '*';
    });
    vm.set('sensorModifierValues', modifierValues);
    vm.set('sensorSelectedConfigInfo', this.buildSensorSelectedConfigInfo(config));
    this.refreshSensorModifierOptions();
    this.syncSensorModifierCombos(modifierValues);
    this.loadPreviewResponse('sensor', config.instconfig, config.source);
    this.refreshSensorConfigStore();
  },

  buildSensorSelectedConfigInfo: function (config) {
    if (!config) return '';
    let lines = [];
    lines.push('Selected sensor configuration:');
    lines.push(config.description || config.instconfig || '');
    let params = config.parameters || {};
    let pkeys = Object.keys(params);
    if (pkeys.length) {
      lines.push('Parameters: ' + pkeys.map(function (k) {
        return k + ' ' + String(params[k]);
      }).join('; '));
    }
    return lines.join('\n');
  },

  syncSensorModifierCombos: function (modifierValues) {
    let form = this.lookupReference('sensorModifierForm');
    if (!form || !modifierValues) return;
    let paramNames = this.getViewModel().get('sensorParameterNames') || [];
    paramNames.forEach(function (pname) {
      let itemId = 'sensor_modifier_' + pname.replace(/[^a-zA-Z0-9_]/g, '_');
      let item = form.down('#' + itemId);
      if (item && modifierValues[pname] !== undefined) {
        let targetValue = String(modifierValues[pname]).trim();
        let comboStore = item.getStore && item.getStore();
        if (comboStore) {
          let idx = comboStore.findExact('value', targetValue);
          if (idx < 0) {
            comboStore.add({ value: targetValue });
          }
        }
        item.suspendEvents(false);
        item.setValue(targetValue);
        if (!item.getRawValue || !item.getRawValue()) {
          item.setRawValue(targetValue);
        }
        item.resumeEvents();
      }
    });
  },

  refreshBreadcrumbArrow: function (breadcrumb, node) {
    if (!breadcrumb || !node || !node.hasChildNodes()) return;
    let depth = node.get ? node.get('depth') : node.data && node.data.depth;
    if (depth != null && breadcrumb._buttons && breadcrumb._buttons[depth]) {
      let btn = breadcrumb._buttons[depth];
      btn.setArrowVisible(true);
      if (btn.updateLayout) btn.updateLayout();
    }
    let nodeId = node.getId && node.getId();
    if (nodeId != null && nodeId !== '') {
      nodeId = String(nodeId);
      let buttons = breadcrumb._buttons;
      if (buttons) {
        for (let i = 0; i < buttons.length; i++) {
          if (buttons[i] && String(buttons[i]._breadcrumbNodeId || '') === nodeId) {
            buttons[i].setArrowVisible(true);
            if (buttons[i].updateLayout) buttons[i].updateLayout();
            break;
          }
        }
      }
    }
    breadcrumb._needsSync = true;
    breadcrumb.setSelection(node);
    if (breadcrumb.updateLayout) breadcrumb.updateLayout();
  },

  appendEmptyPlaceholder: function (node, path, store) {
    if (!node || !path) return;
    let msg = store === this.getStore('dataloggerStore')
      ? 'Manufacturer has no models'
      : 'Manufacturer has no sensors';
    node.appendChild({
      text: msg,
      id: path + '/_empty',
      leaf: true,
      _emptyPlaceholder: true
    });
  },

  setupBreadcrumbLoadOnSelect: function (breadcrumb, store) {
    if (!breadcrumb || !store) return;
    let me = this;
    let url = store === me.getStore('dataloggerStore') ? '/api/nrlv2/dataloggers/' : '/api/nrlv2/sensors/';
    breadcrumb.on('selectionchange', function (cmp, node) {
      if (node && !node.isLeaf() && !node.hasChildNodes()) {
        let nodeId = node.getId();
        let path = (nodeId && nodeId !== '0' && nodeId !== 'root') ? nodeId : '';
        let parts = path ? String(path).split('/') : [];
        if ((store === me.getStore('dataloggerStore') || store === me.getStore('sensorStore')) && parts.length === 2) {
          return;
        }
        Ext.Ajax.request({
          url: url,
          method: 'GET',
          params: path ? { node: path } : {},
          timeout: 35000,
          success: function (resp) {
            let result = JSON.parse(resp.responseText);
            let data = result && result.data;
            if (data && Ext.isArray(data) && data.length > 0) {
              Ext.Array.each(data, function (item) {
                node.appendChild(item);
              });
            } else if (path && path.indexOf('/') < 0) {
              let isOkToAddPlaceholder = !result || result.success !== false || result.errorCode === 'NRLV2_EMPTY_RESULT';
              if (isOkToAddPlaceholder) {
                me.appendEmptyPlaceholder(node, path, store);
              }
            }
            if (node.hasChildNodes()) {
              Ext.defer(function () {
                me.refreshBreadcrumbArrow(cmp, node);
              }, 100);
            }
          },
          failure: function (resp) {
            if (path && path.indexOf('/') < 0) {
              let result;
              try {
                result = (resp && resp.responseText) ? JSON.parse(resp.responseText) : null;
              } catch (e) {
                result = null;
              }
              if (result && result.errorCode === 'NRLV2_EMPTY_RESULT') {
                me.appendEmptyPlaceholder(node, path, store);
                Ext.defer(function () {
                  me.refreshBreadcrumbArrow(cmp, node);
                }, 100);
              }
            }
          }
        });
      }
    });
  },

  getStore: function (name) {
    return this.getViewModel().getStore(name);
  },

  fillRecord: function () {
    let vm = this.getViewModel();
    let record = yasmine.utils.ResponseRecalculateUtil.getRecordFromContext(vm);
    if (!record) {
      return;
    }
    let sensorInstconfig = vm.get('sensorInstconfig');
    let dataloggerInstconfig = vm.get('dataloggerInstconfig');
    if (!sensorInstconfig || !dataloggerInstconfig) return;

    let instconfig = sensorInstconfig + ':' + dataloggerInstconfig;
    let sensorSource = vm.get('sensorSource');
    let dataloggerSource = vm.get('dataloggerSource');
    let source = (sensorSource && sensorSource === dataloggerSource) ? sensorSource : (sensorSource || dataloggerSource);
    let value = { libraryType: 'nrlv2_online', instconfig: instconfig, source: source || undefined };
    record.set('value', yasmine.utils.ResponseRecalculateUtil.withRecalculateFlag(value, vm));
  },

  isDataloggerCompleted: function () {
    return !!this.getViewModel().get('dataloggerPreview');
  },

  isSensorCompleted: function () {
    return !!this.getViewModel().get('sensorPreview');
  },

  getViewModel: function () {
    return this.getView().getViewModel();
  },

  onSensorSelectionChange: function (cmp, node) {
    this.showResponse(node, 'sensor', 'sensorInstconfig');
  },

  onSensorClick: function (item) {
    let node = this.getStore('sensorStore').getNodeById(item._breadcrumbNodeId);
    this.showResponse(node, 'sensor', 'sensorInstconfig');
  },

  onDataloggerSelectionChange: function (cmp, node) {
    this.showResponse(node, 'datalogger', 'dataloggerInstconfig');
  },

  onDataloggerClick: function (item) {
    let node = this.getStore('dataloggerStore').getNodeById(item._breadcrumbNodeId);
    this.showResponse(node, 'datalogger', 'dataloggerInstconfig');
  },

  showResponse: function (node, device, instconfigProperty) {
    let vm = this.getViewModel();
    vm.set(device + 'Preview', null);
    vm.set('channelResponseText', null);
    vm.set('channelResponseImageUrl', null);
    vm.set('channelResponseCsvUrl', null);
    vm.set('channelResponsePlotMessage', null);
    vm.set('responseTree', null);
    vm.set(instconfigProperty, null);
    vm.set(device + 'Source', null);

    if (!node || !node.isLeaf()) {
      Ext.ux.Mediator.fireEvent('parameterEditorController-canSaveButton', false);
      yasmine.utils.ResponseRecalculateUtil.updateWizardActionButtons(vm);
      yasmine.utils.ResponseRecalculateUtil.updateParameterEditorActionButtons(vm);
      return;
    }

    let instconfig = node.get('key');
    let source = node.get('source');
    vm.set(instconfigProperty, instconfig);
    vm.set(device + 'Source', source);
    this.loadPreviewResponse(device, instconfig, source);
  },

  loadPreviewResponse: function (device, instconfig, source) {
    let that = this;
    let params = { instconfig: instconfig };
    if (source) params.source = source;
    Ext.Ajax.request({
      method: 'GET',
      params: params,
      url: `/api/nrlv2/${device}/response/`,
      timeout: 35000,
      success: function (response) {
        that.getViewModel().set(device + 'Preview', response.responseText);
        that.loadChannelResponseIfPossible();
      },
      failure: function (response) {
        that.getViewModel().set(device + 'Preview', 'Error: ' + (response.status || 'Unknown'));
      }
    });
  },

  loadChannelResponseIfPossible: function () {
    let vm = this.getViewModel();
    let sensorInstconfig = vm.get('sensorInstconfig');
    let dataloggerInstconfig = vm.get('dataloggerInstconfig');
    if (!sensorInstconfig || !dataloggerInstconfig) return;

    let instconfig = sensorInstconfig + ':' + dataloggerInstconfig;
    let min = vm.get('minFrequency');
    let max = vm.get('maxFrequency');
    let sensorSource = vm.get('sensorSource');
    let dataloggerSource = vm.get('dataloggerSource');
    let source = (sensorSource && sensorSource === dataloggerSource) ? sensorSource : (sensorSource || dataloggerSource);
    let that = this;

    let params = { instconfig: instconfig, min: min, max: max };
    if (source) params.source = source;
    Ext.Ajax.request({
      method: 'GET',
      params: params,
      url: '/api/nrlv2/channel/response/preview/',
      timeout: 120000,
      success: function (response, options) {
        let result = JSON.parse(response.responseText);
        if (result.success) {
          vm.set('channelResponseText', result.text);
          vm.set('channelResponseImageUrl', result.plot_url || null);
          vm.set('channelResponseCsvUrl', result.csv_url || null);
          vm.set('channelResponsePlotMessage', result.message || null);
          vm.set('responseTree', null);
          Ext.ux.Mediator.fireEvent('parameterEditorController-canSaveButton', true);
          yasmine.utils.ResponseRecalculateUtil.updateWizardActionButtons(vm);
          yasmine.utils.ResponseRecalculateUtil.updateParameterEditorActionButtons(vm);
        } else {
          vm.set('channelResponseImageUrl', null);
          vm.set('channelResponseCsvUrl', null);
          vm.set('channelResponsePlotMessage', null);
          Ext.MessageBox.show({
            title: 'An error occurred',
            msg: result.message || result.errorCode || 'Unknown error',
            buttons: Ext.MessageBox.OK,
            icon: Ext.MessageBox.ERROR
          });
        }
      }
    });
  },

  loadChannelResponsePlot: function () {
    this.loadChannelResponseIfPossible();
  },

  downloadChannelResponsePlot: function () {
    let url = this.getViewModel().get('channelResponseImageUrl');
    if (url) {
      let w = window.open('', '_blank');
      w.location = url;
      w.focus();
    }
  },

  downloadChannelResponseCsv: function () {
    let url = this.getViewModel().get('channelResponseCsvUrl');
    if (url) {
      let w = window.open('', '_self');
      w.location = url;
      w.focus();
    }
  },

  recalculateSensitivity: function () {
    let vm = this.getViewModel();
    let sensorInstconfig = vm.get('sensorInstconfig');
    let dataloggerInstconfig = vm.get('dataloggerInstconfig');
    if (!sensorInstconfig || !dataloggerInstconfig) {
      return;
    }
    let instconfig = sensorInstconfig + ':' + dataloggerInstconfig;
    let sensorSource = vm.get('sensorSource');
    let dataloggerSource = vm.get('dataloggerSource');
    let source = (sensorSource && sensorSource === dataloggerSource)
      ? sensorSource
      : (sensorSource || dataloggerSource);
    let payload = {
      instconfig: instconfig,
      min: vm.get('minFrequency'),
      max: vm.get('maxFrequency')
    };
    if (source) {
      payload.source = source;
    }
    Ext.Ajax.request({
      method: 'POST',
      url: '/api/channel/response/recalculate-sensitivity/',
      jsonData: payload,
      success: function (response) {
        let result = JSON.parse(response.responseText);
        if (!result.success) {
          yasmine.utils.ResponseRecalculateUtil.showRecalculateError(result.message);
          return;
        }
        yasmine.utils.ResponseRecalculateUtil.applyRecalculateResult(vm, result);
      },
      failure: function () {
        yasmine.utils.ResponseRecalculateUtil.showRecalculateError();
      }
    });
  }
});

/* ****************************************************************************
* 2026-09-28, version 4.4.0-beta: ASGSR, Alexey Emanov
* 2026-09-29, version 4.4.0-beta: ASGSR, Alexey Emanov
*
* Shared helpers for Recalculate Sensitivity in response selectors / wizard.
*
* ****************************************************************************/

Ext.define('yasmine.utils.ResponseRecalculateUtil', {
  singleton: true,

  requires: [
    'yasmine.view.xml.builder.parameter.items.channelresponse.RecalculateSensitivityDialog'
  ],

  SELECTOR_XTYPES: [
    'nrlv2-response-selector',
    'nrl-response-selector',
    'arol-response-selector'
  ],

  isSelectorView: function (vm) {
    let view = vm && vm.getView();
    return !!(view && this.SELECTOR_XTYPES.indexOf(view.xtype) >= 0);
  },

  withRecalculateFlag: function (value, vm) {
    if (vm && vm.get('responseTree')) {
      value.recalculateSensitivity = true;
    }
    return value;
  },

  nodeInstanceId: function (record) {
    if (!record || typeof record.get !== 'function') {
      return null;
    }
    let mapped = record.get('nodeId');
    if (mapped !== undefined && mapped !== null && mapped !== '') {
      return mapped;
    }
    let raw = record.get('node_inst_id');
    return raw === undefined ? null : raw;
  },

  getRecordFromContext: function (vm) {
    if (!vm) {
      return null;
    }
    let record = vm.get('record');
    if (record) {
      return record;
    }
    let view = vm.getView();
    if (view && view.up) {
      let parentVm = view.up().lookupViewModel();
      if (parentVm) {
        return parentVm.get('record');
      }
    }
    return null;
  },

  PLOT_POINT_BUDGET: 4000000,
  PLOT_MIN_WITHOUT_MAX_REDUCTION: 0.001,

  limitMaxForPointBudget: function (vm, minHz) {
    if (!vm) {
      return;
    }
    minHz = Number(minHz);
    var maxHz = Number(vm.get('maxFrequency'));
    if (!(minHz > 0) || !(minHz < this.PLOT_MIN_WITHOUT_MAX_REDUCTION) || !(maxHz > 0)) {
      return;
    }
    var limit = this.PLOT_POINT_BUDGET * minHz / 2;
    if (limit < minHz) {
      limit = minHz;
    }
    if (maxHz > limit) {
      vm.set('maxFrequency', limit);
    }
  },

  applyPlotMaxFrequency: function (vm, result) {
    if (!vm || !result) {
      return;
    }
    if (result.max_frequency != null && result.max_frequency !== '') {
      vm.set('maxFrequency', Number(result.max_frequency));
    }
    this.applyPlotStages(vm, result);
  },

  /**
   * Drop Start/End stage selection so the next plot uses the full chain.
   * Call when the channel response is replaced (import RESP, select new).
   */
  clearPlotStageRange: function (vm) {
    if (!vm) {
      return;
    }
    var store = vm.getStore && vm.getStore('plotStageStore');
    if (store && store.loadData) {
      store.loadData([]);
    }
    vm.set({
      plotStartStage: null,
      plotEndStage: null,
      hasPlotStages: false
    });
  },

  applyPlotStages: function (vm, result) {
    if (!vm || !result || !Ext.isArray(result.stages)) {
      return;
    }
    var stages = result.stages;
    var store = vm.getStore('plotStageStore');
    if (!store) {
      store = Ext.create('Ext.data.Store', {
        fields: ['number', 'label'],
        data: []
      });
      vm.setStores({plotStageStore: store});
    }
    store.loadData(stages);

    var numbers = [];
    for (var i = 0; i < stages.length; i++) {
      numbers.push(Number(stages[i].number));
    }
    var first = numbers.length ? numbers[0] : null;
    var last = numbers.length ? numbers[numbers.length - 1] : null;
    var start = vm.get('plotStartStage');
    var end = vm.get('plotEndStage');
    start = start == null || start === '' ? null : Number(start);
    end = end == null || end === '' ? null : Number(end);
    if (start == null || numbers.indexOf(start) < 0) {
      start = first;
    }
    if (end == null || numbers.indexOf(end) < 0) {
      end = last;
    }
    if (start != null && end != null && start > end) {
      end = start;
    }
    vm.set({
      plotStartStage: start,
      plotEndStage: end,
      hasPlotStages: numbers.length > 0
    });
  },

  /**
   * Resolve the editor/selector ViewModel that owns plot stage state.
   * Nested ResponseChart ViewModels inherit stores, so getStore() alone is wrong.
   */
  plotStageViewModel: function (fromCmp) {
    if (!fromCmp) {
      return null;
    }
    var owners = [
      'yasmine-channel-response-field',
      'nrl-response-selector',
      'nrlv2-response-selector',
      'arol-response-selector'
    ];
    var i;
    for (i = 0; i < owners.length; i++) {
      var cmp = fromCmp.up ? fromCmp.up(owners[i]) : null;
      if (!cmp && fromCmp.isXType && fromCmp.isXType(owners[i])) {
        cmp = fromCmp;
      }
      if (cmp && cmp.lookupViewModel) {
        return cmp.lookupViewModel();
      }
    }
    var vm = fromCmp.lookupViewModel && fromCmp.lookupViewModel();
    while (vm && vm.getParent) {
      var parent = vm.getParent();
      if (!parent) {
        break;
      }
      vm = parent;
    }
    return vm || null;
  },

  normalizePlotStageRange: function (vm, changed) {
    if (!vm) {
      return;
    }
    var start = vm.get('plotStartStage');
    var end = vm.get('plotEndStage');
    start = start == null || start === '' ? null : Number(start);
    end = end == null || end === '' ? null : Number(end);
    if (start == null || end == null) {
      return;
    }
    if (start > end) {
      if (changed === 'start') {
        vm.set('plotEndStage', start);
      } else {
        vm.set('plotStartStage', end);
      }
    } else {
      vm.set({
        plotStartStage: start,
        plotEndStage: end
      });
    }
  },

  plotStageParams: function (vm) {
    var params = {};
    if (!vm) {
      return params;
    }
    var start = vm.get('plotStartStage');
    var end = vm.get('plotEndStage');
    if (start != null && start !== '') {
      params.start_stage = Number(start);
    }
    if (end != null && end !== '') {
      params.end_stage = Number(end);
    }
    return params;
  },

  setPlotLoading: function (fromCmp, loading) {
    if (!fromCmp || fromCmp.destroyed) {
      return;
    }
    var ownerVm = this.plotStageViewModel(fromCmp);
    if (!ownerVm && fromCmp.lookupViewModel) {
      ownerVm = fromCmp.lookupViewModel();
    }
    if (ownerVm) {
      ownerVm.set('plotLoading', !!loading);
    }

    var target = null;
    if (fromCmp.isXType && fromCmp.isXType('response-chart')) {
      target = fromCmp;
    } else if (fromCmp.down) {
      target = fromCmp.down('response-chart');
    }
    if (!target && fromCmp.up) {
      target = fromCmp.up('response-chart');
    }
    // Ext LoadMask helps when an image is already on screen; the HTML
    // placeholder covers the empty initial-load state.
    var hasImage = !!(ownerVm && ownerVm.get('channelResponseImageUrl'));
    if (target && !target.destroyed && target.setLoading) {
      if (hasImage || !loading) {
        target.setLoading(loading ? 'Building plot…' : false);
      }
    }
  },

  /**
   * Sync combo values into the owning VM, normalize range, reload plot.
   */
  onPlotStageComboSelect: function (field, which) {
    var ownerVm = this.plotStageViewModel(field);
    if (!ownerVm) {
      return;
    }
    var chart = field.up('response-chart');
    var startField = chart ? chart.down('[reference=plotStartStage]') : null;
    var endField = chart ? chart.down('[reference=plotEndStage]') : null;
    var start = startField ? startField.getValue() : ownerVm.get('plotStartStage');
    var end = endField ? endField.getValue() : ownerVm.get('plotEndStage');
    if (which === 'start') {
      start = field.getValue();
    } else if (which === 'end') {
      end = field.getValue();
    }
    start = start == null || start === '' ? null : Number(start);
    end = end == null || end === '' ? null : Number(end);
    if (start != null && end != null && start > end) {
      if (which === 'start') {
        end = start;
      } else {
        start = end;
      }
    }
    ownerVm.set({
      plotStartStage: start,
      plotEndStage: end
    });
    if (startField && Number(startField.getValue()) !== start) {
      startField.suspendEvent('select');
      startField.setValue(start);
      startField.resumeEvent('select');
    }
    if (endField && Number(endField.getValue()) !== end) {
      endField.suspendEvent('select');
      endField.setValue(end);
      endField.resumeEvent('select');
    }
    var ctrl = field.lookupController();
    if (ctrl && typeof ctrl.loadChannelResponsePlot === 'function') {
      ctrl.loadChannelResponsePlot();
    }
  },

  applyRecalculateResult: function (vm, result) {
    vm.set('channelResponseText', result.text);
    vm.set('channelResponseImageUrl', result.plot_url);
    vm.set('channelResponseCsvUrl', result.csv_url);
    vm.set('channelResponsePlotMessage', null);
    this.applyPlotMaxFrequency(vm, result);
    if (result.data) {
      vm.set('responseTree', result.data);
      if (!vm.get('wizardMode')) {
        if (!this.isSelectorView(vm)) {
          let record = this.getRecordFromContext(vm);
          if (record && record.get('nodeId')) {
            record.set('value', {
              nodeId: record.get('nodeId'),
              response: result.data
            });
          }
        }
        Ext.ux.Mediator.fireEvent('parameterEditorController-canSaveButton', true);
      }
    }
    this.updateWizardActionButtons(vm);
    this.updateParameterEditorActionButtons(vm);
  },

  updateWizardActionButtons: function (vm) {
    if (!vm || !vm.get('wizardMode')) {
      return;
    }
    if (!this.shouldShowRecalculateButton(vm)) {
      Ext.ux.Mediator.fireEvent('wizard-updateActionButtons', []);
      return;
    }
    let controller = vm.getView().getController();
    Ext.ux.Mediator.fireEvent('wizard-updateActionButtons', [
      this.createRecalculateButton(controller)
    ]);
  },

  updateParameterEditorActionButtons: function (vm) {
    if (!vm || vm.get('wizardMode')) {
      return;
    }
    if (!this.shouldShowRecalculateButton(vm)) {
      Ext.ux.Mediator.fireEvent('parameterEditorController-updateActionButtons', []);
      return;
    }
    let controller = vm.getView().getController();
    Ext.ux.Mediator.fireEvent('parameterEditorController-updateActionButtons', [
      this.createRecalculateButton(controller)
    ]);
  },

  shouldShowRecalculateButton: function (vm) {
    if (!vm || !vm.get('channelResponseText') || vm.get('activeSelectorTab') !== 2) {
      return false;
    }
    return !this.isPolynomialResponse(vm);
  },

  isPolynomialResponse: function (vm) {
    if (!vm) {
      return false;
    }
    if (vm.get('isPolynomialResponse')) {
      return true;
    }
    let text = String(vm.get('channelResponseText') || '');
    if (/InstrumentPolynomial|PolynomialResponseStage/i.test(text)) {
      return true;
    }
    let tree = vm.get('responseTree');
    if (tree && Ext.isArray(tree.children)) {
      return tree.children.some(function (child) {
        return /InstrumentPolynomial|Polynomial/i.test(String(child.name || child.tag || ''));
      });
    }
    return false;
  },

  createRecalculateButton: function (controller) {
    let polynomial = controller && controller.getViewModel &&
      this.isPolynomialResponse(controller.getViewModel());
    return Ext.create({
      xtype: 'button',
      text: polynomial ? 'Recalculate unavailable' : 'Recalculate Sensitivity',
      tooltip: polynomial
        ? 'Polynomial responses have no InstrumentSensitivity to recalculate'
        : 'Recalculate Sensitivity',
      iconCls: 'x-fa fa-calculator',
      disabled: !!polynomial,
      handler: function () {
        if (polynomial) {
          Ext.Msg.alert(
            'Recalculate Sensitivity',
            'Polynomial responses have no InstrumentSensitivity. ' +
            'Edit the polynomial coefficients or stages instead.'
          );
          return;
        }
        if (controller && typeof controller.recalculateSensitivity === 'function') {
          controller.recalculateSensitivity();
        }
      }
    });
  },

  showRecalculateError: function (message) {
    Ext.MessageBox.show({
      title: 'An error occurred',
      msg: message || 'Cannot recalculate sensitivity.',
      buttons: Ext.MessageBox.OK,
      icon: Ext.MessageBox.ERROR,
      width: 520
    });
  },

  /**
   * Load ObsPy frequency options and open the two-step Recalculate wizard.
   * handlers: {apply(result), failure?()}.
   */
  promptRecalculateSensitivityWithReview: function (payload, handlers) {
    handlers = handlers || {};
    let that = this;
    Ext.Ajax.request({
      method: 'POST',
      url: '/api/channel/response/recalculate-sensitivity-options/',
      jsonData: payload || {},
      success: function (response) {
        let result;
        try {
          result = JSON.parse(response.responseText);
        } catch (err) {
          that.showRecalculateError('Cannot load recalculation options.');
          return;
        }
        if (!result.success) {
          that.showRecalculateError(result.message || 'Cannot load recalculation options.');
          return;
        }
        Ext.create('yasmine.view.xml.builder.parameter.items.channelresponse.RecalculateSensitivityDialog', {
          options: result,
          payload: payload || {},
          onSave: function (savedResult) {
            if (typeof handlers.apply === 'function') {
              handlers.apply(savedResult);
            }
          }
        }).show();
      },
      failure: function () {
        if (typeof handlers.failure === 'function') {
          handlers.failure();
        } else {
          that.showRecalculateError('Cannot load recalculation options.');
        }
      }
    });
  },

  /**
   * POST recalculate-sensitivity with optional frequencyMode/frequency from the dialog.
   */
  postRecalculateSensitivity: function (payload, choice, handlers) {
    handlers = handlers || {};
    let jsonData = Ext.apply({}, payload || {});
    if (choice && choice.frequencyMode) {
      jsonData.frequencyMode = choice.frequencyMode;
      if (choice.frequencyMode === 'custom' && choice.frequency != null) {
        jsonData.frequency = choice.frequency;
      }
    }
    if (choice && choice.allowZeroGainReset) {
      jsonData.allowZeroGainReset = true;
    }
    Ext.Ajax.request({
      method: 'POST',
      url: '/api/channel/response/recalculate-sensitivity/',
      jsonData: jsonData,
      success: handlers.success,
      failure: handlers.failure
    });
  }
});

/* ****************************************************************************
* 2026-09-28, version 4.4.0-beta: ASGSR, Alexey Emanov
* 2026-09-29, version 4.4.0-beta: ASGSR, Alexey Emanov
*
* Two-step Recalculate Sensitivity wizard: frequency choice, then results.
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.RecalculateSensitivityDialog', {
  extend: 'Ext.window.Window',
  xtype: 'recalculate-sensitivity-dialog',
  requires: [
    'Ext.form.RadioGroup',
    'Ext.form.field.Number',
    'Ext.form.field.Display',
    'Ext.layout.container.Card'
  ],

  title: 'Recalculate Sensitivity',
  modal: true,
  frame: false,
  cls: 'yasmine-window',
  layout: 'card',
  width: 560,
  minWidth: 360,
  maxHeight: 640,
  bodyPadding: 12,
  closeAction: 'destroy',
  resizable: true,
  scrollable: 'y',

  config: {
    options: null,
    payload: null,
    onSave: null
  },

  recalculateResult: null,

  initComponent: function () {
    let options = this.getOptions() || {};
    let that = this;
    this.items = [
      {
        xtype: 'form',
        itemId: 'frequencyStep',
        border: false,
        scrollable: 'y',
        layout: {
          type: 'vbox',
          align: 'stretch'
        },
        items: [
          {
            xtype: 'component',
            cls: 'recalculate-sensitivity-warning',
            margin: '0 0 12 0',
            html: [
              '<p style="margin:0 0 8px 0;">',
              'ObsPy Auto does <b>not</b> use the stored InstrumentSensitivity frequency. ',
              'It takes the first-stage normalization frequency and caps it ',
              'by Nyquist&nbsp;/&nbsp;2 (so <code>f&nbsp;≤&nbsp;Fs&nbsp;/&nbsp;4</code>).',
              '</p>',
              '<p style="margin:0;color:#555;">',
              'That is why the recalculated frequency can look unexpected ',
              '(for example when sample rate is non-standard). Use Custom frequency ',
              'to evaluate at the reported InstrumentSensitivity frequency.',
              '</p>'
            ].join('')
          },
          {
            xtype: 'displayfield',
            fieldLabel: 'Reported sensitivity',
            labelWidth: 180,
            value: that.formatReported(options)
          },
          {
            xtype: 'displayfield',
            fieldLabel: 'First-stage normalization frequency',
            labelWidth: 180,
            value: that.formatHz(options.normalization_frequency)
          },
          {
            xtype: 'displayfield',
            fieldLabel: 'Response sample rate',
            labelWidth: 180,
            value: that.formatHz(options.sample_rate)
          },
          {
            xtype: 'displayfield',
            fieldLabel: 'Predicted Auto frequency',
            labelWidth: 180,
            value: that.formatHz(options.auto_frequency)
          },
          {
            xtype: 'checkboxfield',
            itemId: 'allowZeroGainReset',
            hidden: !options.zero_sensitivity_value,
            boxLabel: 'Reset InstrumentSensitivity value 0 → 1.0 before recalculate (required; ObsPy cannot evaluate zero)',
            checked: false,
            margin: '0 0 12 0'
          },
          {
            xtype: 'radiogroup',
            itemId: 'frequencyMode',
            fieldLabel: 'Recalculation frequency',
            labelWidth: 180,
            columns: 1,
            vertical: true,
            simpleValue: true,
            local: true,
            value: 'auto',
            items: [
              {
                boxLabel: 'Auto (ObsPy default — ignores stored InstrumentSensitivity.frequency)',
                name: 'frequencyMode',
                inputValue: 'auto',
                checked: true
              },
              {boxLabel: 'Custom frequency', name: 'frequencyMode', inputValue: 'custom'}
            ],
            listeners: {
              change: function (group, value) {
                let field = that.down('#customFrequency');
                if (field) {
                  field.setDisabled(value !== 'custom');
                  if (value === 'custom') {
                    field.focus();
                  }
                }
              }
            }
          },
          {
            xtype: 'numberfield',
            itemId: 'customFrequency',
            fieldLabel: 'Frequency (Hz)',
            labelWidth: 180,
            allowDecimals: true,
            decimalPrecision: 8,
            minValue: 1e-12,
            allowBlank: false,
            hideTrigger: true,
            keyNavEnabled: false,
            mouseWheelEnabled: false,
            disabled: true,
            value: options.auto_frequency != null
              ? options.auto_frequency
              : (options.reported_sensitivity_frequency != null
                ? options.reported_sensitivity_frequency
                : 1)
          }
        ]
      },
      {
        xtype: 'form',
        itemId: 'resultsStep',
        border: false,
        scrollable: 'y',
        layout: {
          type: 'vbox',
          align: 'stretch'
        },
        items: [
          {
            xtype: 'displayfield',
            itemId: 'previousSensitivity',
            fieldLabel: 'Previous sensitivity',
            labelWidth: 180,
            value: 'n/a'
          },
          {
            xtype: 'displayfield',
            itemId: 'previousFrequency',
            fieldLabel: 'Previous frequency',
            labelWidth: 180,
            value: 'n/a'
          },
          {
            xtype: 'displayfield',
            itemId: 'newSensitivity',
            fieldLabel: 'New sensitivity',
            labelWidth: 180,
            value: 'n/a'
          },
          {
            xtype: 'displayfield',
            itemId: 'newFrequency',
            fieldLabel: 'New frequency',
            labelWidth: 180,
            value: 'n/a'
          },
          {
            xtype: 'displayfield',
            itemId: 'percentChange',
            fieldLabel: 'Change',
            labelWidth: 180,
            value: 'n/a'
          }
        ]
      }
    ];
    this.buttons = [
      {
        itemId: 'cancelButton',
        text: 'Cancel',
        handler: function () {
          that.close();
        }
      },
      {
        itemId: 'recalculateButton',
        text: 'Recalculate',
        ui: 'default-toolbar',
        handler: function () {
          that.onRecalculateClick();
        }
      },
      {
        itemId: 'saveButton',
        text: 'Save recalculation results',
        ui: 'default-toolbar',
        hidden: true,
        handler: function () {
          that.onSaveClick();
        }
      }
    ];
    this.callParent(arguments);
  },

  formatHz: function (value) {
    if (value == null || value === '') {
      return 'n/a';
    }
    let number = Number(value);
    if (!(number > 0)) {
      return 'n/a';
    }
    return number + ' Hz';
  },

  formatReported: function (options) {
    let value = options.reported_sensitivity_value;
    let freq = options.reported_sensitivity_frequency;
    if (value == null || value === '') {
      return 'n/a';
    }
    let valueText = Number(value);
    if (isNaN(valueText)) {
      valueText = value;
    }
    if (freq == null || freq === '') {
      return String(valueText);
    }
    return valueText + ' @ ' + Number(freq) + ' Hz';
  },

  formatSensitivity: function (value, frequency) {
    if (value == null || value === '') {
      return 'n/a';
    }
    let valueText = Number(value);
    if (isNaN(valueText)) {
      valueText = value;
    }
    if (frequency == null || frequency === '') {
      return String(valueText);
    }
    return valueText + ' @ ' + Number(frequency) + ' Hz';
  },

  formatPercentChange: function (previousValue, newValue) {
    if (previousValue == null || previousValue === '' || newValue == null || newValue === '') {
      return 'n/a';
    }
    let previous = Number(previousValue);
    let next = Number(newValue);
    if (isNaN(previous) || isNaN(next) || previous === 0) {
      return 'n/a';
    }
    let percent = (next - previous) / previous * 100;
    let rounded = Math.round(percent * 100) / 100;
    let sign = rounded > 0 ? '+' : '';
    return sign + rounded + '%';
  },

  readChoice: function () {
    let modeGroup = this.down('#frequencyMode');
    let mode = modeGroup ? modeGroup.getValue() : 'auto';
    let choice = {frequencyMode: mode === 'custom' ? 'custom' : 'auto'};
    let options = (typeof this.getOptions === 'function' ? this.getOptions() : null) || {};
    if (options.zero_sensitivity_value) {
      let allow = this.down('#allowZeroGainReset');
      if (!allow || !allow.getValue()) {
        return {error: 'Confirm resetting InstrumentSensitivity value 0 → 1.0 before recalculate.'};
      }
      choice.allowZeroGainReset = true;
    }
    if (choice.frequencyMode === 'custom') {
      let field = this.down('#customFrequency');
      let freq = field ? field.getValue() : null;
      if (freq == null || !(Number(freq) > 0)) {
        return null;
      }
      choice.frequency = Number(freq);
    }
    return choice;
  },

  onRecalculateClick: function () {
    let choice = this.readChoice();
    if (choice && choice.error) {
      Ext.Msg.alert('Recalculate Sensitivity', choice.error);
      return;
    }
    if (!choice) {
      Ext.Msg.alert('Recalculate Sensitivity', 'Enter a frequency greater than zero.');
      return;
    }
    let that = this;
    let options = this.getOptions() || {};
    this.setLoading('Recalculating...');
    yasmine.utils.ResponseRecalculateUtil.postRecalculateSensitivity(
      this.getPayload() || {},
      choice,
      {
        success: function (response) {
          that.setLoading(false);
          if (that.destroyed) {
            return;
          }
          let result;
          try {
            result = JSON.parse(response.responseText);
          } catch (err) {
            yasmine.utils.ResponseRecalculateUtil.showRecalculateError();
            return;
          }
          if (!result.success) {
            yasmine.utils.ResponseRecalculateUtil.showRecalculateError(result.message);
            return;
          }
          that.showResultsStep({
            value: options.reported_sensitivity_value,
            frequency: options.reported_sensitivity_frequency
          }, result);
        },
        failure: function () {
          that.setLoading(false);
          if (!that.destroyed) {
            yasmine.utils.ResponseRecalculateUtil.showRecalculateError();
          }
        }
      }
    );
  },

  showResultsStep: function (previous, result) {
    previous = previous || {};
    result = result || {};
    this.recalculateResult = result;
    let prevSens = this.down('#previousSensitivity');
    let prevFreq = this.down('#previousFrequency');
    let newSens = this.down('#newSensitivity');
    let newFreq = this.down('#newFrequency');
    let change = this.down('#percentChange');
    if (prevSens) {
      prevSens.setValue(this.formatSensitivity(previous.value, previous.frequency));
    }
    if (prevFreq) {
      prevFreq.setValue(this.formatHz(previous.frequency));
    }
    if (newSens) {
      newSens.setValue(this.formatSensitivity(result.sensitivity_value, result.sensitivity_frequency));
    }
    if (newFreq) {
      newFreq.setValue(this.formatHz(result.sensitivity_frequency));
    }
    if (change) {
      change.setValue(this.formatPercentChange(previous.value, result.sensitivity_value));
    }
    this.setTitle('Recalculate Sensitivity Results');
    let recalculateButton = this.down('#recalculateButton');
    let saveButton = this.down('#saveButton');
    if (recalculateButton) {
      recalculateButton.setHidden(true);
    }
    if (saveButton) {
      saveButton.setHidden(false);
    }
    this.getLayout().setActiveItem('resultsStep');
  },

  onSaveClick: function () {
    let onSave = this.getOnSave();
    let result = this.recalculateResult;
    this.close();
    if (typeof onSave === 'function') {
      onSave(result);
    }
  }
});

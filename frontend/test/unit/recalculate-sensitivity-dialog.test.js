/* 2026-09-28, version 4.4.0-beta: ASGSR, Alexey Emanov
 * 2026-09-29, version 4.4.0-beta: ASGSR, Alexey Emanov */
'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {loadSingleton} = require('./ext-singleton');

const dialog = loadSingleton(
  'classic/src/view/builder/parameter/items/channelresponse/RecalculateSensitivityDialog.js'
);

test('formatHz shows n/a for missing or non-positive values', () => {
  assert.equal(dialog.formatHz(null), 'n/a');
  assert.equal(dialog.formatHz(''), 'n/a');
  assert.equal(dialog.formatHz(0), 'n/a');
  assert.equal(dialog.formatHz(-1), 'n/a');
});

test('formatHz appends Hz for positive numbers', () => {
  assert.equal(dialog.formatHz(4.2458333), '4.2458333 Hz');
  assert.equal(dialog.formatHz('10'), '10 Hz');
});

test('formatReported shows value at frequency', () => {
  assert.equal(dialog.formatReported({}), 'n/a');
  assert.equal(dialog.formatReported({
    reported_sensitivity_value: 100,
    reported_sensitivity_frequency: null
  }), '100');
  assert.equal(dialog.formatReported({
    reported_sensitivity_value: 79894100000,
    reported_sensitivity_frequency: 4.2458333
  }), '79894100000 @ 4.2458333 Hz');
});

test('formatPercentChange reports signed percent or n/a', () => {
  assert.equal(dialog.formatPercentChange(null, 100), 'n/a');
  assert.equal(dialog.formatPercentChange(0, 100), 'n/a');
  assert.equal(dialog.formatPercentChange(100, 110), '+10%');
  assert.equal(dialog.formatPercentChange(100, 99.5), '-0.5%');
  assert.equal(dialog.formatPercentChange(100, 100), '0%');
});

test('readChoice returns Auto without a frequency field', () => {
  const win = Object.assign({}, dialog, {
    down: function () {
      return {getValue: function () { return 'auto'; }};
    }
  });
  const choice = win.readChoice();
  assert.equal(choice.frequencyMode, 'auto');
  assert.equal(choice.frequency, undefined);
});

test('readChoice returns custom frequency', () => {
  const win = Object.assign({}, dialog, {
    down: function (id) {
      if (id === '#frequencyMode') {
        return {getValue: function () { return 'custom'; }};
      }
      if (id === '#customFrequency') {
        return {getValue: function () { return 1.5; }};
      }
      return null;
    }
  });
  const choice = win.readChoice();
  assert.equal(choice.frequencyMode, 'custom');
  assert.equal(choice.frequency, 1.5);
});

test('readChoice requires zero-gain confirm when flagged', () => {
  const win = Object.assign({}, dialog, {
    getOptions: function () {
      return {zero_sensitivity_value: true};
    },
    down: function (id) {
      if (id === '#frequencyMode') {
        return {getValue: function () { return 'auto'; }};
      }
      if (id === '#allowZeroGainReset') {
        return {getValue: function () { return false; }};
      }
      return null;
    }
  });
  const blocked = win.readChoice();
  assert.ok(blocked.error);
  assert.match(blocked.error, /0 → 1\.0/);

  const allowed = Object.assign({}, win, {
    down: function (id) {
      if (id === '#frequencyMode') {
        return {getValue: function () { return 'auto'; }};
      }
      if (id === '#allowZeroGainReset') {
        return {getValue: function () { return true; }};
      }
      return null;
    }
  }).readChoice();
  assert.equal(allowed.frequencyMode, 'auto');
  assert.equal(allowed.allowZeroGainReset, true);
});

test('showResultsStep switches card and fills fields', () => {
  const fields = {};
  let activeItem = null;
  let title = null;
  let recalculateHidden = false;
  let saveHidden = true;
  const win = Object.assign({}, dialog, {
    down: function (id) {
      if (id === '#previousSensitivity' || id === '#previousFrequency' ||
          id === '#newSensitivity' || id === '#newFrequency' || id === '#percentChange') {
        return {
          setValue: function (value) {
            fields[id] = value;
          }
        };
      }
      if (id === '#recalculateButton') {
        return {
          setHidden: function (hidden) {
            recalculateHidden = hidden;
          }
        };
      }
      if (id === '#saveButton') {
        return {
          setHidden: function (hidden) {
            saveHidden = hidden;
          }
        };
      }
      return null;
    },
    setTitle: function (value) {
      title = value;
    },
    getLayout: function () {
      return {
        setActiveItem: function (item) {
          activeItem = item;
        }
      };
    }
  });
  win.showResultsStep(
    {value: 100, frequency: 1},
    {sensitivity_value: 110, sensitivity_frequency: 1.5}
  );
  assert.equal(activeItem, 'resultsStep');
  assert.equal(title, 'Recalculate Sensitivity Results');
  assert.equal(recalculateHidden, true);
  assert.equal(saveHidden, false);
  assert.equal(fields['#previousSensitivity'], '100 @ 1 Hz');
  assert.equal(fields['#newSensitivity'], '110 @ 1.5 Hz');
  assert.equal(fields['#percentChange'], '+10%');
  assert.equal(win.recalculateResult.sensitivity_value, 110);
});

test('onSaveClick closes and invokes onSave with the result', () => {
  const saved = [];
  const result = {sensitivity_value: 1, sensitivity_frequency: 2};
  const win = Object.assign({}, dialog, {
    recalculateResult: result,
    getOnSave: function () {
      return function (value) { saved.push(value); };
    },
    close: function () {}
  });
  win.onSaveClick();
  assert.equal(saved.length, 1);
  assert.equal(saved[0], result);
});

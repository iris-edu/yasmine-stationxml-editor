/* 2026-09-27, version 4.4.0-beta: ASGSR, Alexey Emanov */
'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {loadSingleton} = require('./ext-singleton');

const events = [];
const yasmine = {
  Globals: {
    DatePrintLongFormat: 'old-long',
    DatePrintShortFormat: 'old-short',
    BuilderViewMode: 'tree'
  },
  utils: {
    DateUtil: {
      refreshGuiDates: function () {
        events.push('dates');
      }
    }
  }
};

const settings = loadSingleton('app/utils/SettingsUtil.js', {
  yasmine: yasmine,
  Ext: {
    GlobalEvents: {
      fireEvent: function (name) {
        events.push(name);
      }
    }
  }
});

test('SettingsUtil.applySettings copies formats and view mode', () => {
  settings.applySettings({
    general__date_format_long: 'Y-m-d H:i:s',
    general__date_format_short: 'Y-m-d',
    general__xml_view_mode: 'card'
  });
  assert.equal(yasmine.Globals.DatePrintLongFormat, 'Y-m-d H:i:s');
  assert.equal(yasmine.Globals.DatePrintShortFormat, 'Y-m-d');
  assert.equal(yasmine.Globals.BuilderViewMode, 'card');
  assert.deepEqual(events, ['dates', 'yasmine-settings-applied']);
});

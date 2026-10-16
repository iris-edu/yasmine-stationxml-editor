/* 2026-09-27, version 4.4.0-beta: ASGSR, Alexey Emanov */
'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {loadSingleton} = require('./ext-singleton');

const yasmine = {
  Globals: {
    DatePrintShortFormat: 'Y-m-d',
    DatePrintLongFormat: 'Y-m-d H:i:s',
    DateReadFormat: 'Y-m-d\\TH:i:s'
  }
};

const dateUtil = loadSingleton('app/utils/DateUtil.js', {
  yasmine: yasmine,
  Ext: {
    isDate: function (value) {
      return value instanceof Date;
    },
    Date: {
      parse: function (value) {
        return value === 'bad' ? null : new Date('2020-01-02T03:04:05Z');
      },
      format: function (date, format) {
        return format + ':' + date.getUTCFullYear();
      }
    },
    ComponentQuery: {
      query: function () {
        return [];
      }
    }
  }
});

test('DateUtil.guiFormat selects the short and long patterns', () => {
  assert.equal(dateUtil.guiFormat('short'), 'Y-m-d');
  assert.equal(dateUtil.guiFormat('long'), 'Y-m-d H:i:s');
});

test('DateUtil.formatShort returns empty for missing or unparseable values', () => {
  assert.equal(dateUtil.formatShort(''), '');
  assert.equal(dateUtil.formatShort(null), '');
  assert.equal(dateUtil.formatShort('bad'), '');
  const parsed = dateUtil.formatShort('2020-01-02T03:04:05');
  assert.equal(parsed, 'Y-m-d:2020');
  const direct = dateUtil.formatShort(new Date('2020-05-01T00:00:00Z'));
  assert.equal(direct, 'Y-m-d:2020');
});

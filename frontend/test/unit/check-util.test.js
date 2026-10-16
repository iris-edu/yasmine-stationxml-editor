/* 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov */
'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {loadSingleton} = require('./ext-singleton');

const CheckUtil = loadSingleton('app/utils/CheckUtil.js');

test('CheckUtil.isEmpty treats blank values as empty', () => {
  assert.equal(CheckUtil.isEmpty(''), true);
  assert.equal(CheckUtil.isEmpty(null), true);
  assert.equal(CheckUtil.isEmpty(undefined), true);
  assert.equal(CheckUtil.isEmpty('   '), true);
  assert.equal(CheckUtil.isEmpty('NVS'), false);
  assert.equal(CheckUtil.isEmpty(0), false);
});

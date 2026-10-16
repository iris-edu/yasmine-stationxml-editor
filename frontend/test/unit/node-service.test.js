/* 2026-09-27, version 4.4.0-beta: ASGSR, Alexey Emanov */
'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {loadSingleton} = require('./ext-singleton');

const service = loadSingleton('app/services/NodeService.js');

test('NodeService.parentIdFromPath returns the node above the current one', () => {
  const parent = service.statics.parentIdFromPath;
  assert.equal(parent(null), 0);
  assert.equal(parent([{id: 1}]), 0);
  assert.equal(parent([{id: 10}, {id: 20}]), 10);
  assert.equal(parent([{id: 10}, {id: 20}, {id: 30}]), 20);
});

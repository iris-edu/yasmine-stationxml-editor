/* 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov */
'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {loadSingleton} = require('./ext-singleton');

const NodeTypeConverter = loadSingleton('app/utils/NodeTypeConverter.js', {
  yasmine: {
    NodeTypeEnum: {network: 1, station: 2, channel: 3},
    Globals: {NotApplicable: 'N/A'}
  }
});

test('NodeTypeConverter maps titles and children', () => {
  assert.equal(NodeTypeConverter.toString(1), 'Network');
  assert.equal(NodeTypeConverter.toString(2), 'Station');
  assert.equal(NodeTypeConverter.toString(3), 'Channel');
  assert.equal(NodeTypeConverter.toString(99), 'N/A');
  assert.equal(NodeTypeConverter.getChild(0), 1);
  assert.equal(NodeTypeConverter.getChild(1), 2);
  assert.equal(NodeTypeConverter.getChild(2), 3);
  assert.equal(NodeTypeConverter.getChild(3), null);
  assert.equal(NodeTypeConverter.getParent(1), 0);
  assert.equal(NodeTypeConverter.getParent(3), 2);
  assert.equal(NodeTypeConverter.getChildTitle(1), 'Station');
  assert.match(NodeTypeConverter.toIcon(1), /fa-connectdevelop/);
  assert.match(NodeTypeConverter.toIcon(99), /fa-history/);
});

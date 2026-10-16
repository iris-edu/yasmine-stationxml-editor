/* 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov */
'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {loadSingleton} = require('./ext-singleton');

const util = loadSingleton('app/utils/ResponseSchemaUtil.js');
util.descriptor = {
  namespace: 'http://www.fdsn.org/xml/station/1',
  types: {
    Gain: {kind: 'simple', valueType: 'number'},
    Stage: {
      kind: 'complex',
      attributes: {
        number: {required: true, type: 'integer'}
      },
      children: []
    },
    Output: {kind: 'simple', enum: ['VEL', 'ACC']}
  }
};

test('ResponseSchemaUtil parses Clark and prefixed names', () => {
  assert.equal(util.getLocalName('{http://example.org}Extra'), 'Extra');
  assert.equal(util.getNamespace('{http://example.org}Extra'), 'http://example.org');
  assert.equal(util.getLocalName('fs:Name'), 'Name');
  assert.equal(util.getNamespace('fs:Name'), '__prefixed__');
  assert.equal(util.getLocalName('Stage'), 'Stage');
  assert.equal(util.getNamespace('Stage'), null);
});

test('ResponseSchemaUtil marks foreign names', () => {
  assert.equal(util.isForeignName('{http://example.org}Extra'), true);
  assert.equal(util.isForeignName('{http://www.fdsn.org/xml/station/1}Stage'), false);
  assert.match(util.displayName('{http://example.org}Extra'), /foreign namespace/);
});

test('defaultScalarValue uses enum and numeric defaults', () => {
  assert.equal(util.defaultScalarValue('Gain'), '0');
  assert.equal(util.defaultScalarValue('Output'), 'VEL');
  assert.equal(util.defaultScalarValue('Unknown'), '');
});

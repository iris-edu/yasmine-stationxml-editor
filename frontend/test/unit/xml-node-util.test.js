/* 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov */
'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {loadSingleton} = require('./ext-singleton');

const XmlNodeUtil = loadSingleton('app/utils/XmlNodeUtil.js');

function node(key, value) {
  const data = {key: key};
  data[key] = value;
  return {data: data};
}

test('XmlNodeUtil classifies plain, array, and object values', () => {
  const plain = node('Gain', 1.2);
  assert.equal(XmlNodeUtil.isPlainValue(plain), true);
  assert.equal(XmlNodeUtil.canHaveValue(plain), true);
  assert.equal(XmlNodeUtil.getValue(plain), '1.2');

  const array = node('Name', {children: ['STS-2']});
  assert.equal(XmlNodeUtil.isArrayValue(array), true);
  assert.equal(XmlNodeUtil.getValue(array), 'STS-2');

  const nested = node('Stage', {children: [{Gain: 1}]});
  assert.equal(XmlNodeUtil.isPlainValue(nested), false);
  assert.equal(XmlNodeUtil.isArrayValue(nested), false);
  assert.equal(XmlNodeUtil.canHaveValue(nested), false);
});

test('XmlNodeUtil.getNodeTitle encodes HTML from keys and values', () => {
  const unsafe = node('<script>', '<img>');
  const title = XmlNodeUtil.getNodeTitle(unsafe);
  assert.equal(title.includes('<script>'), false);
  assert.equal(title.includes('<img>'), false);
  assert.equal(title.includes('&lt;script&gt;'), true);
  assert.equal(title.includes('&lt;img&gt;'), true);
});

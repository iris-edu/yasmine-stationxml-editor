/* 2026-09-27, version 4.4.0-beta: ASGSR, Alexey Emanov */
'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {loadSingleton} = require('./ext-singleton');

const util = loadSingleton('app/utils/ResponsiveUtil.js');

function size(width, height) {
  util.getSize = function () {
    return {width: width, height: height};
  };
}

test('ResponsiveUtil classifies viewport width', () => {
  size(320, 800);
  assert.equal(util.getViewportClass(), 'xs');
  size(400, 800);
  assert.equal(util.getViewportClass(), 'sm');
  size(800, 800);
  assert.equal(util.getViewportClass(), 'md');
  assert.equal(util.useStackLayout(), false);
  assert.equal(util.useToolbarWrap(), true);
  size(1100, 800);
  assert.equal(util.getViewportClass(), 'lg');
  size(1400, 800);
  assert.equal(util.getViewportClass(), 'xl');
  size(2000, 800);
  assert.equal(util.getViewportClass(), 'xxl');
  size(3000, 800);
  assert.equal(util.getViewportClass(), 'uw');
});

test('ResponsiveUtil stacks narrow or short viewports and splits wide ones', () => {
  size(320, 800);
  assert.equal(util.useStackLayout(), true);
  assert.equal(util.useTopHeader(), true);
  assert.equal(util.useComparisonSplit(), false);
  size(1400, 400);
  assert.equal(util.useStackLayout(), true);
  assert.equal(util.isCompactHeight(), true);
  size(1400, 900);
  assert.equal(util.useStackLayout(), false);
  assert.equal(util.useTopHeader(), false);
  assert.equal(util.useComparisonSplit(), true);
});

// Hierarchy Select Epoch uses full-width second row under xs/sm/compact-height
// (ChildrenControlController wrapEpoch: width < 768 || compact height).
test('ResponsiveUtil phone widths match Hierarchy Epoch wrap thresholds', () => {
  size(320, 812);
  assert.equal(util.getViewportClass(), 'xs');
  assert.equal(util.getWidth() < 768, true);
  assert.equal(util.useToolbarWrap(), true);
  size(375, 812);
  assert.equal(util.getViewportClass(), 'sm');
  assert.equal(util.getWidth() < 768, true);
  assert.equal(util.useToolbarWrap(), true);
  size(767, 500);
  assert.equal(util.useStackLayout(), true);
  assert.equal(util.getWidth() <= util.STACK_MAX, true);
  size(767, 499);
  assert.equal(util.isCompactHeight(), true);
  assert.equal(util.useToolbarWrap(), true);
  size(1024, 800);
  assert.equal(util.useToolbarWrap(), false);
  assert.equal(util.getWidth() < 768, false);
});

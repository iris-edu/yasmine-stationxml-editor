/* 2026-09-27, version 4.4.0-beta: ASGSR, Alexey Emanov */
'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {loadSingleton} = require('./ext-singleton');

function load(ajax) {
  return loadSingleton('app/utils/ValidatorUtil.js', {
    Ext: {
      Ajax: {
        request: function (cfg) {
          ajax(cfg);
        }
      }
    }
  });
}

test('ValidatorUtil.validate reports a message when the request fails', () => {
  const util = load(function (cfg) {
    cfg.failure();
  });
  const result = util.validate(3, 'code', 'BHZ', true);
  assert.equal(result.success, false);
  assert.equal(result.message.length, 1);
  assert.equal(result.message[0], 'Validation is unavailable.');
});

test('ValidatorUtil.validate keeps a server message and fills a missing one', () => {
  const ok = load(function (cfg) {
    cfg.success({responseText: JSON.stringify({success: true, message: []})});
  });
  assert.equal(ok.validate(3, 'code', 'BHZ', true).message.length, 0);

  const bare = load(function (cfg) {
    cfg.success({responseText: JSON.stringify({success: false})});
  });
  assert.equal(bare.validate(3, 'code', '', true).message[0], 'Validation is unavailable.');

  const broken = load(function (cfg) {
    cfg.success({responseText: '{'});
  });
  assert.equal(broken.validate(3, 'code', '', true).success, false);
});

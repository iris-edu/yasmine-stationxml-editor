/* 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

function htmlEncode(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function createExtStub() {
  return {
    define: function (name, cfg) {
      this._lastDefined = cfg;
    },
    htmlEncode: htmlEncode,
    isString: function (value) {
      return typeof value === 'string';
    },
    isArray: Array.isArray,
    create: function () {
      return {};
    },
    apply: function (object, config) {
      object = object || {};
      if (config) {
        Object.keys(config).forEach(function (key) {
          object[key] = config[key];
        });
      }
      return object;
    },
    Ajax: {
      request: function () {}
    },
    callback: function (fn, scope, args) {
      if (typeof fn === 'function') {
        fn.apply(scope, args || []);
      }
    },
    Array: {
      each: function (arr, fn, scope) {
        (arr || []).forEach(function (item, index) {
          fn.call(scope, item, index);
        });
      },
      findBy: function (arr, fn) {
        return (arr || []).find(fn) || null;
      },
      clone: function (arr) {
        return (arr || []).slice();
      },
      filter: function (arr, fn, scope) {
        return (arr || []).filter(function (item, index) {
          return fn.call(scope, item, index);
        });
      },
      some: function (arr, fn, scope) {
        return (arr || []).some(function (item, index) {
          return fn.call(scope, item, index);
        });
      },
      contains: function (arr, value) {
        return (arr || []).indexOf(value) >= 0;
      }
    },
    Object: {
      each: function (obj, fn, scope) {
        Object.keys(obj || {}).forEach(function (key) {
          fn.call(scope, key, obj[key]);
        });
      },
      getSize: function (obj) {
        return Object.keys(obj || {}).length;
      }
    },
    MessageBox: {show: function () {}, OK: 1, ERROR: 2},
    ux: {Mediator: {fireEvent: function () {}}}
  };
}

function loadSingleton(relativePath, extras) {
  const filePath = path.join(__dirname, '..', '..', relativePath);
  const Ext = createExtStub();
  const contextExtras = Object.assign({}, extras || {});
  if (contextExtras.Ext) {
    Object.assign(Ext, contextExtras.Ext);
    delete contextExtras.Ext;
  }
  const context = Object.assign({
    Ext: Ext,
    console: console
  }, contextExtras);
  vm.runInNewContext(fs.readFileSync(filePath, 'utf8'), context, {filename: filePath});
  const cfg = Ext._lastDefined || {};
  const instance = Object.assign({
    callParent: function () {},
    waiters: [],
    descriptor: null
  }, cfg);
  return instance;
}

module.exports = {htmlEncode, loadSingleton};

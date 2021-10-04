/**
 * The main application class. An instance of this class is created by app.js
 * when it calls Ext.application(). This is the ideal place to handle
 * application launch and initialization details.
 */
Ext.ns('yasmine.Globals');
yasmine.Globals.NotApplicable = '';
yasmine.Globals.DatePrintLongFormat = 'Y-m-d H:i:s';
yasmine.Globals.DatePrintShortFormat = 'Y-m-d';
yasmine.Globals.DateReadFormat = 'd/m/Y H:i:s';
yasmine.Globals.Settings = null;
yasmine.Globals.LocationColorScale = null; // Very ugly solution. TODO: find a better way to implement it

Ext.util.JSON.encodeDate = function (o) {
  return '"' + Ext.Date.format(o, yasmine.Globals.DateReadFormat) + '"'
};

Ext.define('yasmine.Application', {
  extend: 'Ext.app.Application',
  name: 'yasmine',
  requires: ['Ext.grid.plugin.RowEditing', 'yasmine.view.settings.Settings', 'yasmine.utils.SettingsUtil'],
  quickTips: false,
  platformConfig: {
    desktop: {
      quickTips: true
    }
  },
  defaultToken: 'xmls',
  stores: [
    // TODO: add global / shared stores here
  ],
  init: function () {
    Ext.Ajax.setTimeout(120000);
    Ext.Ajax.on('requestexception', function (conn, response, options) {
      var message;
      try {
        message = JSON.parse(response.responseText).data;
      } catch (error) {
        message = 'Please try again or contact your administrator.'
      }
      Ext.MessageBox.show({
        title: 'An error occurred',
        msg: message,
        buttons: Ext.MessageBox.OK,
        icon: Ext.MessageBox['ERROR']
      });
    });
    Ext.Error.handle = function (err) {
      Ext.MessageBox.show({
        title: 'An error occurred',
        msg: 'Please try again or contact your administrator.',
        buttons: Ext.MessageBox.OK,
        icon: Ext.MessageBox['ERROR']
      });
    };
    var requestCounter = 0;
    Ext.Ajax.on('beforerequest', function () {
      if (requestCounter === 0) {
        var splashscreen = Ext.getBody().mask('Loading...');
        splashscreen.dom.style.zIndex = '99999';
        splashscreen.show({
          delay: 700
        });
      }
      requestCounter++;
    }, this);
    Ext.Ajax.on('requestcomplete', function (conn, response) {
      requestCounter--;
      if (requestCounter === 0) {
        Ext.getBody().unmask();
      }
      if (response.responseText) {
        let result = {};
        try {
          result = JSON.parse(response.responseText);
        } catch (e) {
          result = {};
        }

        response.responseData = {};
        if (result.hasOwnProperty('success') && !result.success) {
          Ext.MessageBox.show({
            title: 'An error occurred',
            msg: result.message,
            buttons: Ext.MessageBox.OK,
            icon: Ext.MessageBox['ERROR']
          });
        } else if (result.hasOwnProperty('data')) {
          response.responseData = Object.assign({}, result.data);
        }
      }
    }, this);
    Ext.Ajax.on('requestexception', function () {
      requestCounter--;
      if (requestCounter === 0) {
        Ext.getBody().unmask();
      }
    }, this);
  },
  launch: function () {
    yasmine.services.SettingsService.initSettings();

    Ext.define('Override.form.field.VTypes', {
      override: 'Ext.form.field.VTypes',
      phoneNumber: function (value) {
        return this.phoneNumberRe.test(value);
      },
      phoneNumberRe: /[0-9]+-[0-9]+/i,
      phoneNumberText: 'Not a valid phone number. Must be in the form "[0-9]+-[0-9]+", e.g. 1234-5678',
      phoneNumberMask: /[\d\s-\d\s]/i
    });
  },
  onAppUpdate: function () {
    Ext.Msg.confirm('Application Update', 'This application has an update, reload?', function (choice) {
      if (choice === 'yes') {
        window.location.reload();
      }
    });
  }
});

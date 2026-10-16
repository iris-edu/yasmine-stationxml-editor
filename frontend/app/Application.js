/**
 * 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
 * The main application class. An instance of this class is created by app.js
 * when it calls Ext.application(). This is the ideal place to handle
 * application launch and initialization details.
 *
 * NRLv2 online support (2026): ASGSR, Alexey Emanov.
 */
Ext.ns('yasmine.Globals');
if (Ext.Loader && Ext.Loader.setPath) {
  Ext.Loader.setPath({
    'yasmine.view.xml.builder.parameter.items.measurement.MeasurementMetadata':
      'app/view/builder/parameter/items/measurement/MeasurementMetadata.js',
    'yasmine.view.xml.builder.parameter.items.measurement.MeasurementMetadataWindow':
      'classic/src/view/builder/parameter/items/measurement/MeasurementMetadataWindow.js',
    'yasmine.view.xml.builder.parameter.items.measurement.MeasurementMetadataWindowController':
      'app/view/builder/parameter/items/measurement/MeasurementMetadataWindowController.js',
    'yasmine.view.xml.builder.parameter.items.measurement.MeasurementMetadataWindowModel':
      'app/view/builder/parameter/items/measurement/MeasurementMetadataWindowModel.js',
    'yasmine.view.xml.builder.parameter.items.float.StationXmlDoubleField':
      'classic/src/view/builder/parameter/items/float/StationXmlDoubleField.js'
  });
}
yasmine.Globals.NotApplicable = '';
yasmine.Globals.DatePrintLongFormat = 'Y-m-d H:i:s';
yasmine.Globals.DatePrintShortFormat = 'Y-m-d';
yasmine.Globals.DateReadFormat = 'Y-m-d\\TH:i:s';
yasmine.Globals.BuilderViewMode = 1;
yasmine.Globals.Settings = null;
yasmine.Globals.LocationColorScale = (function () {
  var colors = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
  ];
  var assigned = {};
  var next = 0;
  return function (key) {
    var id = String(key);
    if (!Object.prototype.hasOwnProperty.call(assigned, id)) {
      assigned[id] = colors[next % colors.length];
      next += 1;
    }
    return assigned[id];
  };
}());
yasmine.Globals.logoUrl = function (file) {
  file = file || 'logo-mark.svg';
  try {
    if (Ext.manifest && typeof Ext.manifest === 'object' && Ext.manifest.resources) {
      return Ext.getResourcePath('images/' + file, 'shared');
    }
  } catch (e) {}
  return 'resources/images/' + file;
};

Ext.util.JSON.encodeDate = function (o) {
  return '"' + Ext.Date.format(o, yasmine.Globals.DateReadFormat) + '"'
};

Ext.define('yasmine.Application', {
  extend: 'Ext.app.Application',
  name: 'yasmine',
  requires: [
    'Ext.grid.plugin.RowEditing',
    'overrides.grid.plugin.RowEditing',
    'overrides.form.field.Radio',
    'yasmine.view.settings.Settings',
    'yasmine.utils.SettingsUtil',
    'yasmine.utils.ResponsiveUtil'
  ],
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
    // Suppress WAI-ARIA compatibility warnings (menu button SPACE/ENTER conflict)
    Ext.ariaWarn = Ext.emptyFn;

    // Ensure Radio has setTooltip for bindings (Ext.form.field.Radio lacks it; Bindable requires it)
    var Radio = Ext.form && Ext.form.field && Ext.form.field.Radio;
    if (Radio) {
      Radio.prototype.setTooltip = function (tip) {
        this.tooltip = tip;
        if (this.rendered && this.el && this.el.dom) {
          if (tip) {
            this.el.dom.setAttribute('data-qtip', Ext.htmlEncode(tip));
          } else {
            this.el.dom.removeAttribute('data-qtip');
          }
        }
      };
    }

    Ext.Ajax.setTimeout(120000);
    Ext.Ajax.on('requestexception', function (conn, response, options) {
      var message;
      try {
        var parsed = JSON.parse(response.responseText || '{}');
        message = parsed.data || parsed.message || parsed.reason || 'Please try again or contact your administrator.';
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
    Ext.Ajax.on('requestcomplete', function (conn, response) {
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
            msg: result.message || result.data || 'Please try again or contact your administrator.',
            buttons: Ext.MessageBox.OK,
            icon: Ext.MessageBox['ERROR']
          });
        } else if (result.hasOwnProperty('data')) {
          response.responseData = Array.isArray(result.data)
            ? result.data.slice()
            : Object.assign({}, result.data);
        }
      }
    }, this);
  },
  launch: function () {
    try {
      yasmine.utils.ResponsiveUtil.bind();
    } catch (bindError) {
      Ext.log.warn('ResponsiveUtil.bind failed: ' + bindError);
    }
    try {
      yasmine.services.SettingsService.initSettings();
    } catch (settingsError) {
      Ext.log.warn('SettingsService.initSettings failed: ' + settingsError);
    }
    if (typeof window.yasmineHideSplash === 'function') {
      Ext.defer(window.yasmineHideSplash, 1);
    }

    Ext.define('Override.form.field.VTypes', {
      override: 'Ext.form.field.VTypes',
      phoneNumber: function (value) {
        return this.phoneNumberRe.test(value);
      },
      phoneNumberRe: /^[0-9]+-[0-9]+$/,
      phoneNumberText: 'Phone number must contain two digit groups separated by a hyphen.',
      phoneNumberMask: /[\d-]/,
      phoneNumberFormat: function (value) {
        if (value == null || value === '') {
          return value;
        }
        var text = String(value);
        if (this.phoneNumberRe.test(text) || text.indexOf('-') !== -1) {
          return text;
        }
        var digits = text.replace(/\D/g, '');
        if (digits.length < 4) {
          return text;
        }
        return digits.substring(0, 3) + '-' + digits.substring(3);
      },
      countryCode: function (value) {
        return this.countryCodeRe.test(value);
      },
      countryCodeRe: /^[+-]?\d+$/,
      countryCodeText: 'Country code must be an integer.',
      countryCodeMask: /[+\-\d]/,
      areaCode: function (value) {
        return this.areaCodeRe.test(value);
      },
      areaCodeRe: /^[+-]?\d+$/,
      areaCodeText: 'Area code must be an integer.',
      areaCodeMask: /[+\-\d]/
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

/* 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov */
describe('yasmine.utils.HelpUtil', function () {
  afterEach(function () {
    Ext.ComponentQuery.query('stationxml-help').forEach(function (win) {
      win.destroy();
    });
    Ext.ComponentQuery.query('main_help').forEach(function (win) {
      win.destroy();
    });
  });

  it('keeps GATITO /api/help and StationXML help separate', function () {
    expect(yasmine.help.HelpModel.prototype.proxy.url).toBe('/api/help/');
    expect(yasmine.utils.HelpUtil.helpMe).toBeDefined();
    expect(yasmine.utils.HelpUtil.stationXmlHelpMe).toBeDefined();
  });

  it('reuses one StationXML help window for context updates', function () {
    var created = [];
    var originalCreate = Ext.create;
    Ext.create = function (config) {
      var win = originalCreate.call(Ext, config);
      created.push(win);
      win.showContext = Ext.emptyFn;
      return win;
    };
    try {
      yasmine.utils.HelpUtil.stationXmlHelpMe({
        nodeType: 1,
        parameterName: 'code'
      }, 'Network code');
      yasmine.utils.HelpUtil.stationXmlHelpMe({
        nodeType: 2,
        parameterName: 'site'
      }, 'Station site');
    } finally {
      Ext.create = originalCreate;
    }
    expect(created.length).toBe(1);
    expect(Ext.ComponentQuery.query('stationxml-help').length).toBe(1);
  });
});

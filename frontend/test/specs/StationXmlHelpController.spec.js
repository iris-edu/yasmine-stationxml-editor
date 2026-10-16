/* 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov */
describe('yasmine.view.help.stationxml.StationXmlHelpController', function () {
  it('renders exact singular XML element names', function () {
    var controller = Ext.create('yasmine.view.help.stationxml.StationXmlHelpController');
    var html;
    try {
      html = controller.renderEntry({
        kind: 'element',
        xmlName: 'Comment',
        path: '/FDSNStationXML/Network/Comment',
        effectiveOccurs: {min: 0, max: null},
        documentation: {
          description: [],
          warnings: []
        },
        conditions: [],
        facets: {}
      });
    } finally {
      if (controller.destroy) {
        controller.destroy();
      }
    }
    expect(html).toContain('<h2><code>Comment</code></h2>');
    expect(html).not.toContain('<h2><code>Comments</code></h2>');
  });

  it('loads the versioned StationXML help catalog', function () {
    var controller = Ext.create('yasmine.view.help.stationxml.StationXmlHelpController');
    var requested;
    var originalLoad = yasmine.utils.StationXmlHelpContext.load;
    yasmine.utils.StationXmlHelpContext.load = function (success) {
      requested = true;
      Ext.callback(success, controller, [{
        rootPath: '/FDSNStationXML',
        tree: {xmlName: 'FDSNStationXML', path: '/FDSNStationXML', children: []},
        nodes: {'/FDSNStationXML': {xmlName: 'FDSNStationXML'}}
      }]);
    };
    try {
      controller.loadContext({path: '/FDSNStationXML/Network'}, 'Network');
    } finally {
      yasmine.utils.StationXmlHelpContext.load = originalLoad;
      if (controller.destroy) {
        controller.destroy();
      }
    }
    expect(requested).toBe(true);
  });
});

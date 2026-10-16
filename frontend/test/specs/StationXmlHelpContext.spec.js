/* 2026-09-24, version 4.3.2-beta: ASGSR, Alexey Emanov */
describe('yasmine.utils.StationXmlHelpContext', function () {
  var Context;

  beforeEach(function () {
    Context = yasmine.utils.StationXmlHelpContext;
  });

  it('joins element and attribute relative paths', function () {
    expect(Context.joinPath('/FDSNStationXML/Network/Comment', 'Author'))
      .toBe('/FDSNStationXML/Network/Comment/Author');
    expect(Context.joinPath('/FDSNStationXML/Network/Comment', '@subject'))
      .toBe('/FDSNStationXML/Network/Comment/@subject');
  });

  it('resolves editor contexts to the nearest catalog path', function () {
    var catalog = {
      rootPath: '/FDSNStationXML',
      editorContexts: {
        network: {
          comments: '/FDSNStationXML/Network/Comment'
        }
      },
      nodes: {
        '/FDSNStationXML': {},
        '/FDSNStationXML/Network': {},
        '/FDSNStationXML/Network/Comment': {},
        '/FDSNStationXML/Network/Comment/Author': {}
      }
    };
    expect(Context.resolve({
      nodeType: 1,
      parameterName: 'comments',
      relativePath: 'Author/Name'
    }, catalog)).toBe('/FDSNStationXML/Network/Comment/Author');
  });

  it('maps Comment and Operator fields, including person prefixes', function () {
    expect(Context.relativePathForField('comments', {
      stationXmlRelativePath: '@subject'
    })).toBe('@subject');
    expect(Context.relativePathForField('operators', {
      getFieldLabel: function () { return 'Website'; }
    })).toBe('WebSite');
    expect(Context.relativePathForField('person', {
      getFieldLabel: function () { return 'Name'; }
    }, 'Author')).toBe('Author/Name');
    expect(Context.relativePathForField('person', {
      getFieldLabel: function () { return 'Email'; }
    }, 'Contact')).toBe('Contact/Email');
  });

  it('turns XML names into spaced field labels', function () {
    expect(Context.xmlNameToLabel('startDate')).toBe('Start Date');
    expect(Context.xmlNameToLabel('ClockDrift')).toBe('Clock Drift');
    expect(Context.xmlNameToLabel('sourceID')).toBe('Source ID');
    expect(Context.xmlNameToLabel('ModuleURI')).toBe('Module URI');
    expect(Context.xmlNameToLabel('SampleRateRatio/NumberSamples'))
      .toBe('Sample Rate Ratio / Number Samples');
    expect(Context.labelForParameter('start_date')).toBe('Start Date');
    expect(Context.labelForParameter('clock_drift_in_seconds_per_sample'))
      .toBe('Clock Drift');
    expect(Context.labelForParameter('sample_rate_ratio_number_samples'))
      .toBe('Sample Rate Ratio / Number Samples');
  });

  it('uses collection labels without changing XML element labels', function () {
    expect(Context.labelForParameter('comments')).toBe('Comments');
    expect(Context.labelForParameter('identifiers')).toBe('Identifiers');
    expect(Context.labelForParameter('operators')).toBe('Operators');
    expect(Context.labelForParameter('external_references'))
      .toBe('External References');
    expect(Context.labelForParameter('types')).toBe('Types');
    expect(Context.labelForParameter('equipments')).toBe('Equipment');
    expect(Context.labelForParameter('start_date')).toBe('Start Date');
    expect(Context.xmlNameToLabel('Comment')).toBe('Comment');
    expect(Context.relabelMessages(
      ["Attribute 'comments' required."],
      'comments'
    )).toEqual(["Attribute 'Comments' required."]);
  });

  it('prefers catalog editor contexts when a help catalog is loaded', function () {
    var original = Context.catalog;
    Context.catalog = {
      editorContexts: {
        channel: {
          clock_drift_in_seconds_per_sample:
            '/FDSNStationXML/Network/Station/Channel/ClockDrift'
        }
      }
    };
    try {
      expect(Context.labelForParameter(
        'clock_drift_in_seconds_per_sample',
        3
      )).toBe('Clock Drift');
    } finally {
      Context.catalog = original;
    }
  });

  it('builds wizard help for the field being filled', function () {
    var stationCode = Context.wizardHelpRequest({
      nodeType: 2,
      itemId: 'code',
      fieldLabel: 'Station Code'
    });
    expect(stationCode.context.parameterName).toBe('code');
    expect(stationCode.context.nodeType).toBe(2);
    expect(stationCode.search).toBe('Code');
    expect(stationCode.title).toBe('Station Code');

    var channelDip = Context.wizardHelpRequest({
      nodeType: 3,
      itemId: 'dip2',
      validationAttr: 'dip',
      fieldLabel: 'Dip'
    });
    expect(channelDip.context.parameterName).toBe('dip');
    expect(channelDip.search).toBe('Dip');

    var gain = Context.wizardHelpRequest({
      nodeType: 3,
      fieldLabel: 'Final_Sample_Rate',
      inDataloggerModifier: true
    });
    expect(gain.context.parameterName).toBe('data_logger');
    expect(gain.search).toBe('Final Sample Rate');

    var orientation = Context.wizardHelpRequest({
      nodeType: 3,
      reference: 'orientationApplies',
      fieldLabel: 'Orientation applies'
    });
    expect(orientation.context.parameterName).toBe('dip');
    expect(orientation.title).toBe('Channel Dip');

    var dip = Context.wizardHelpRequest({
      nodeType: 3,
      fieldLabel: 'Dip'
    });
    expect(dip.context.parameterName).toBe('dip');
    expect(dip.context.nodeType).toBe(3);
    expect(dip.search).toBe('Dip');
    expect(dip.title).toBe('Channel Dip');

    var empty = Context.wizardHelpRequest({nodeType: 1});
    expect(empty.context.path).toBe('/FDSNStationXML/Network');
    expect(empty.search).toBe('');
  });

  it('scores schema search so spaced labels match XML names', function () {
    var startDate = {
      xmlName: 'startDate',
      path: '/FDSNStationXML/Network/@startDate',
      kind: 'attribute'
    };
    var sampleRate = {
      xmlName: 'SampleRate',
      path: '/FDSNStationXML/Network/Station/Channel/SampleRate',
      kind: 'element'
    };
    expect(Context.searchScore(startDate, 'Start Date')).toBeGreaterThan(0);
    expect(Context.searchScore(sampleRate, 'Final Sample Rate')).toBeGreaterThan(0);
    expect(Context.searchScore(sampleRate, 'Latitude')).toBe(0);
    expect(Context.searchScore(startDate, 'Start Date'))
      .toBeGreaterThan(Context.searchScore({
        xmlName: 'Description',
        path: '/FDSNStationXML/Network/Description'
      }, 'Start Date'));
  });

  it('builds response tree paths from stage keys', function () {
    var node = {
      get: function (name) { return name === 'key' ? 'StageGain' : null; },
      parentNode: {
        get: function (name) { return name === 'key' ? 'Stage' : null; },
        parentNode: {
          get: function (name) { return name === 'key' ? 'Response' : null; }
        }
      }
    };
    expect(Context.buildResponsePath(
      node,
      '/FDSNStationXML/Network/Station/Channel/Response',
      'resourceId'
    )).toBe(
      '/FDSNStationXML/Network/Station/Channel/Response/Stage/StageGain/@resourceId'
    );
  });
});

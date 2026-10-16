/* 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov */
'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

function joinPath(basePath, relativePath) {
  const base = String(basePath || '').replace(/\/+$/, '');
  const relative = String(relativePath == null ? '' : relativePath).replace(/^\/+/, '');
  if (!relative) {
    return base;
  }
  if (relative.charAt(0) === '@') {
    return base + '/@' + relative.substring(1);
  }
  return base + '/' + relative;
}

function nearestKnownPath(path, catalog) {
  if (!catalog || !path) {
    return null;
  }
  const nodes = catalog.nodes || {};
  let candidate = String(path);
  while (candidate) {
    if (nodes[candidate]) {
      return candidate;
    }
    candidate = candidate.replace(/\/(?:@)?[^/]+$/, '');
  }
  return catalog.rootPath || null;
}

function buildResponsePath(treeNode, basePath, attributeName) {
  const parts = [];
  let node = treeNode;
  while (node) {
    const key = node.key;
    if (key && key !== 'Response') {
      parts.unshift(key);
    }
    node = node.parentNode;
  }
  let path = String(basePath || '').replace(/\/+$/, '');
  if (parts.length) {
    path += '/' + parts.join('/');
  }
  if (attributeName) {
    path += '/@' + String(attributeName).replace(/^@/, '');
  }
  return path;
}

function relativePathForField(parameterName, field, baseRelative) {
  const parameter = String(parameterName || '').toLowerCase();
  let relative;
  if (field && field.stationXmlRelativePath !== undefined) {
    relative = field.stationXmlRelativePath;
  } else {
    const mappings = {
      comments: {
        value: 'Value',
        subject: '@subject'
      },
      operators: {
        website: 'WebSite',
        agency: 'Agency'
      },
      person: {
        name: 'Name',
        email: 'Email'
      }
    };
    const label = String((field && field.fieldLabel) || '')
      .replace(/<[^>]*>/g, '')
      .replace(/[^a-z0-9]+/gi, ' ')
      .trim()
      .toLowerCase();
    relative = mappings[parameter] && mappings[parameter][label];
  }
  if (baseRelative) {
    return joinPath(baseRelative, relative);
  }
  return relative;
}

test('joinPath appends elements and attributes', () => {
  assert.equal(
    joinPath('/FDSNStationXML/Network/Comment', 'Author'),
    '/FDSNStationXML/Network/Comment/Author'
  );
  assert.equal(
    joinPath('/FDSNStationXML/Network/Comment', '@subject'),
    '/FDSNStationXML/Network/Comment/@subject'
  );
  assert.equal(joinPath('/FDSNStationXML/Network', ''), '/FDSNStationXML/Network');
});

test('nearestKnownPath walks to the closest catalog node', () => {
  const catalog = {
    rootPath: '/FDSNStationXML',
    nodes: {
      '/FDSNStationXML': {},
      '/FDSNStationXML/Network': {},
      '/FDSNStationXML/Network/Comment': {}
    }
  };
  assert.equal(
    nearestKnownPath('/FDSNStationXML/Network/Comment/Author/Name', catalog),
    '/FDSNStationXML/Network/Comment'
  );
  assert.equal(nearestKnownPath('/unknown', catalog), '/FDSNStationXML');
});

test('buildResponsePath includes stages and attributes', () => {
  const stage = {
    key: 'StageGain',
    parentNode: {key: 'Stage', parentNode: {key: 'Response'}}
  };
  assert.equal(
    buildResponsePath(
      stage,
      '/FDSNStationXML/Network/Station/Channel/Response',
      'resourceId'
    ),
    '/FDSNStationXML/Network/Station/Channel/Response/Stage/StageGain/@resourceId'
  );
});

function xmlSuffixFromPath(path) {
  const prefixes = [
    '/FDSNStationXML/Network/Station/Channel',
    '/FDSNStationXML/Network/Station',
    '/FDSNStationXML/Network',
    '/FDSNStationXML'
  ];
  const text = String(path || '');
  for (const prefix of prefixes) {
    if (text === prefix) {
      return text.replace(/^.*\//, '');
    }
    if (text.startsWith(prefix + '/')) {
      return text.substring(prefix.length + 1);
    }
  }
  return text.replace(/^.*\//, '');
}

function xmlNameToLabel(xmlName) {
  return String(xmlName || '')
    .replace(/^@/, '')
    .split('/')
    .map((token) => {
      const spaced = String(token || '')
        .replace(/^@/, '')
        .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
        .replace(/([A-Z]+)([A-Z][a-z])/g, '$1 $2')
        .replace(/_/g, ' ')
        .trim();
      return spaced.replace(/(^| )([a-z])/g, (_, space, letter) => space + letter.toUpperCase());
    })
    .filter(Boolean)
    .join(' / ');
}

const COLLECTION_UI_LABELS = {
  comments: 'Comments',
  identifiers: 'Identifiers',
  operators: 'Operators',
  external_references: 'External References',
  types: 'Types',
  equipments: 'Equipment'
};

function labelForParameter(parameterName, xmlSuffix) {
  const name = String(parameterName || '');
  return COLLECTION_UI_LABELS[name] || xmlNameToLabel(xmlSuffix || name);
}

test('xmlNameToLabel splits canonical XML names into words', () => {
  assert.equal(xmlNameToLabel('startDate'), 'Start Date');
  assert.equal(xmlNameToLabel('@startDate'), 'Start Date');
  assert.equal(xmlNameToLabel('ClockDrift'), 'Clock Drift');
  assert.equal(xmlNameToLabel('sourceID'), 'Source ID');
  assert.equal(xmlNameToLabel('ModuleURI'), 'Module URI');
  assert.equal(xmlNameToLabel('schemaVersion'), 'Schema Version');
  assert.equal(
    xmlNameToLabel('SampleRateRatio/NumberSamples'),
    'Sample Rate Ratio / Number Samples'
  );
  assert.equal(
    xmlNameToLabel('CalibrationUnits/Name'),
    'Calibration Units / Name'
  );
  assert.equal(xmlNameToLabel('SelectedNumberStations'), 'Selected Number Stations');
  assert.equal(xmlNameToLabel('PreAmplifier'), 'Pre Amplifier');
});

test('labelForParameter distinguishes UI collections from XML names', () => {
  assert.equal(labelForParameter('comments', 'Comment'), 'Comments');
  assert.equal(labelForParameter('identifiers', 'Identifier'), 'Identifiers');
  assert.equal(labelForParameter('operators', 'Operator'), 'Operators');
  assert.equal(
    labelForParameter('external_references', 'ExternalReference'),
    'External References'
  );
  assert.equal(labelForParameter('types', 'Type'), 'Types');
  assert.equal(labelForParameter('equipments', 'Equipment'), 'Equipment');
  assert.equal(labelForParameter('start_date', 'startDate'), 'Start Date');
  assert.equal(xmlNameToLabel('Comment'), 'Comment');
});

test('xmlSuffixFromPath keeps nested XML names after the node prefix', () => {
  assert.equal(
    xmlSuffixFromPath('/FDSNStationXML/Network/Station/Channel/@startDate'),
    '@startDate'
  );
  assert.equal(
    xmlSuffixFromPath(
      '/FDSNStationXML/Network/Station/Channel/SampleRateRatio/NumberSamples'
    ),
    'SampleRateRatio/NumberSamples'
  );
  assert.equal(xmlSuffixFromPath('/FDSNStationXML/ModuleURI'), 'ModuleURI');
});

test('relativePathForField prefers explicit paths and person prefixes', () => {
  assert.equal(
    relativePathForField('comments', {stationXmlRelativePath: '@subject'}),
    '@subject'
  );
  assert.equal(
    relativePathForField('comments', {fieldLabel: 'Value'}),
    'Value'
  );
  assert.equal(
    relativePathForField('person', {fieldLabel: 'Name'}, 'Author'),
    'Author/Name'
  );
  assert.equal(
    relativePathForField('person', {fieldLabel: 'Email'}, 'Contact'),
    'Contact/Email'
  );
});

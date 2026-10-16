/* ****************************************************************************
* 2026-09-24, version 4.3.2-beta: ASGSR, Alexey Emanov
*
* StationXML 1.2 help catalog loading and editor-context resolution.
*
* ****************************************************************************/

Ext.define('yasmine.utils.StationXmlHelpContext', {
  singleton: true,

  catalog: null,
  loading: false,
  waiters: null,

  constructor: function () {
    this.waiters = [];
    return this.callParent(arguments);
  },

  load: function (success, failure, scope) {
    var me = this;
    if (me.catalog) {
      Ext.callback(success, scope || me, [me.catalog]);
      return;
    }

    me.waiters.push({
      success: success,
      failure: failure,
      scope: scope
    });
    if (me.loading) {
      return;
    }

    me.loading = true;
    Ext.Ajax.request({
      url: '/api/stationxml/help/1.2/',
      method: 'GET',
      success: function (response) {
        var waiters = me.waiters;
        me.waiters = [];
        me.loading = false;
        try {
          me.catalog = Ext.decode(response.responseText);
          Ext.Array.each(waiters, function (waiter) {
            Ext.callback(
              waiter.success,
              waiter.scope || me,
              [me.catalog]
            );
          });
        } catch (error) {
          Ext.Array.each(waiters, function (waiter) {
            Ext.callback(waiter.failure, waiter.scope || me, [error]);
          });
        }
      },
      failure: function (response) {
        var waiters = me.waiters;
        me.waiters = [];
        me.loading = false;
        Ext.Array.each(waiters, function (waiter) {
          Ext.callback(
            waiter.failure,
            waiter.scope || me,
            [response]
          );
        });
      }
    });
  },

  clearCache: function () {
    this.catalog = null;
    this.loading = false;
    this.waiters = [];
  },

  nodeTypeName: function (nodeType) {
    if (nodeType === 1 || nodeType === '1') {
      return 'network';
    }
    if (nodeType === 2 || nodeType === '2') {
      return 'station';
    }
    if (nodeType === 3 || nodeType === '3') {
      return 'channel';
    }
    return String(nodeType || '').toLowerCase();
  },

  joinPath: function (basePath, relativePath) {
    var base = String(basePath || '').replace(/\/+$/, '');
    var relative = String(relativePath == null ? '' : relativePath)
      .replace(/^\/+/, '');
    if (!relative) {
      return base;
    }
    if (relative.charAt(0) === '@') {
      return base + '/@' + relative.substring(1);
    }
    return base + '/' + relative;
  },

  resolve: function (context, catalog) {
    catalog = catalog || this.catalog;
    if (!catalog) {
      return null;
    }
    if (Ext.isString(context)) {
      return this.nearestKnownPath(context, catalog);
    }
    context = context || {};
    if (context.path) {
      return this.nearestKnownPath(context.path, catalog);
    }

    var level = this.nodeTypeName(context.nodeType);
    var mappings = catalog.editorContexts || {};
    var base = mappings[level] &&
      mappings[level][context.parameterName];
    if (!base && context.rootField) {
      base = mappings.root && mappings.root[context.rootField];
    }
    if (!base) {
      return null;
    }
    return this.nearestKnownPath(
      this.joinPath(base, context.relativePath),
      catalog
    );
  },

  nearestKnownPath: function (path, catalog) {
    catalog = catalog || this.catalog;
    if (!catalog || !path) {
      return null;
    }
    var nodes = catalog.nodes || {};
    var candidate = String(path);
    while (candidate) {
      if (nodes[candidate]) {
        return candidate;
      }
      candidate = candidate.replace(/\/(?:@)?[^/]+$/, '');
    }
    return catalog.rootPath || null;
  },

  buildResponsePath: function (treeNode, basePath, attributeName) {
    var parts = [];
    var node = treeNode;
    while (node) {
      var key = node.get ? node.get('key') : (
        node.data ? node.data.key : node.key
      );
      if (key && key !== 'Response') {
        parts.unshift(key);
      }
      node = node.parentNode;
    }
    var path = String(basePath || '').replace(/\/+$/, '');
    if (parts.length) {
      path += '/' + parts.join('/');
    }
    if (attributeName) {
      path += '/@' + String(attributeName).replace(/^@/, '');
    }
    return path;
  },

  relativePathForField: function (parameterName, field, baseRelative) {
    var parameter = String(parameterName || '').toLowerCase();
    var relative;
    if (field && field.stationXmlRelativePath !== undefined) {
      relative = field.stationXmlRelativePath;
    } else {
      relative = this._mappedRelativePath(parameter, field);
    }
    if (baseRelative) {
      return this.joinPath(baseRelative, relative);
    }
    return relative;
  },

  _mappedRelativePath: function (parameter, field) {
    var fieldName = field && field.getName ? field.getName() : '';
    var label = field && field.getFieldLabel ?
      field.getFieldLabel() : (field && field.fieldLabel);
    label = String(label || fieldName || '')
      .replace(/<[^>]*>/g, '')
      .replace(/[^a-z0-9]+/gi, ' ')
      .trim()
      .toLowerCase();

    var mappings = {
      site: {
        name: 'Name',
        description: 'Description',
        town: 'Town',
        county: 'County',
        region: 'Region',
        country: 'Country'
      },
      comments: {
        subject: '@subject',
        comment: 'Value',
        value: 'Value',
        id: '@id',
        'id optional': '@id',
        'effective start date': 'BeginEffectiveTime',
        'effective end date': 'EndEffectiveTime',
        author: 'Author'
      },
      operators: {
        website: 'WebSite',
        agency: 'Agency',
        contact: 'Contact'
      },
      person: {
        name: 'Name',
        agency: 'Agency',
        email: 'Email',
        'country code': 'CountryCode',
        'area code': 'AreaCode',
        'phone number': 'PhoneNumber',
        description: '@description'
      },
      equipment: {
        type: 'Type',
        description: 'Description',
        model: 'Model',
        manufacturer: 'Manufacturer',
        vendor: 'Vendor',
        'serial number': 'SerialNumber',
        'resource id': '@resourceId',
        'installation date': 'InstallationDate',
        'removal date': 'RemovalDate',
        'calibration date': 'CalibrationDate'
      },
      equipments: {
        type: 'Type',
        description: 'Description',
        model: 'Model',
        manufacturer: 'Manufacturer',
        vendor: 'Vendor',
        'serial number': 'SerialNumber',
        'resource id': '@resourceId',
        'installation date': 'InstallationDate',
        'removal date': 'RemovalDate',
        'calibration date': 'CalibrationDate'
      },
      external_references: {
        uri: 'URI',
        description: 'Description'
      },
      identifiers: {
        value: '',
        type: '@type'
      }
    };

    if (parameter === 'sensor' || parameter === 'pre_amplifier' ||
        parameter === 'data_logger') {
      parameter = 'equipment';
    }
    return mappings[parameter] && mappings[parameter][label];
  },

  remember: function (owner, path) {
    if (owner && path) {
      owner.stationXmlHelpPath = path;
    }
    return path;
  },

  remembered: function (owner) {
    return owner && owner.stationXmlHelpPath;
  },

  EDITOR_XML_SUFFIXES: {
    code: '@code',
    alternate_code: '@alternateCode',
    historical_code: '@historicalCode',
    source_id: '@sourceID',
    start_date: '@startDate',
    end_date: '@endDate',
    restricted_status: '@restrictedStatus',
    description: 'Description',
    identifiers: 'Identifier',
    comments: 'Comment',
    data_availability: 'DataAvailability',
    operators: 'Operator',
    total_number_of_stations: 'TotalNumberStations',
    selected_number_of_stations: 'SelectedNumberStations',
    latitude: 'Latitude',
    longitude: 'Longitude',
    elevation: 'Elevation',
    site: 'Site',
    water_level: 'WaterLevel',
    vault: 'Vault',
    geology: 'Geology',
    equipment: 'Equipment',
    equipments: 'Equipment',
    external_references: 'ExternalReference',
    creation_date: 'CreationDate',
    termination_date: 'TerminationDate',
    total_number_of_channels: 'TotalNumberChannels',
    selected_number_of_channels: 'SelectedNumberChannels',
    location_code: '@locationCode',
    depth: 'Depth',
    azimuth: 'Azimuth',
    dip: 'Dip',
    types: 'Type',
    sample_rate: 'SampleRate',
    sample_rate_ratio_number_samples: 'SampleRateRatio/NumberSamples',
    sample_rate_ratio_number_seconds: 'SampleRateRatio/NumberSeconds',
    clock_drift_in_seconds_per_sample: 'ClockDrift',
    calibration_units: 'CalibrationUnits/Name',
    calibration_units_description: 'CalibrationUnits/Description',
    sensor: 'Sensor',
    pre_amplifier: 'PreAmplifier',
    data_logger: 'DataLogger',
    response: 'Response',
    created: 'Created',
    module: 'Module',
    sender: 'Sender',
    source: 'Source',
    uri: 'ModuleURI',
    schema_version: '@schemaVersion'
  },

  xmlSuffixFromPath: function (path) {
    var prefixes = [
      '/FDSNStationXML/Network/Station/Channel',
      '/FDSNStationXML/Network/Station',
      '/FDSNStationXML/Network',
      '/FDSNStationXML'
    ];
    var text = String(path || '');
    var i;
    for (i = 0; i < prefixes.length; i++) {
      if (text === prefixes[i]) {
        return text.replace(/^.*\//, '');
      }
      if (text.indexOf(prefixes[i] + '/') === 0) {
        return text.substring(prefixes[i].length + 1);
      }
    }
    return text.replace(/^.*\//, '');
  },

  xmlSuffixForParameter: function (parameterName, nodeType) {
    var name = String(parameterName || '');
    var catalog = this.catalog;
    var level;
    var path;
    if (catalog && catalog.editorContexts && name) {
      level = this.nodeTypeName(nodeType);
      path = catalog.editorContexts[level] &&
        catalog.editorContexts[level][name];
      if (!path && catalog.editorContexts.root) {
        path = catalog.editorContexts.root[name];
      }
      if (path) {
        return this.xmlSuffixFromPath(path);
      }
    }
    return this.EDITOR_XML_SUFFIXES[name] || null;
  },

  xmlNameToLabel: function (xmlName) {
    var parts = String(xmlName || '')
      .replace(/^@/, '')
      .split('/')
      .map(function (token) {
        var spaced = String(token || '')
          .replace(/^@/, '')
          .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
          .replace(/([A-Z]+)([A-Z][a-z])/g, '$1 $2')
          .replace(/_/g, ' ')
          .trim();
        return spaced.replace(/(^| )([a-z])/g, function (_, space, letter) {
          return space + letter.toUpperCase();
        });
      })
      .filter(Boolean);
    return parts.join(' / ');
  },

  snakeNameToLabel: function (name) {
    var text = String(name == null ? '' : name).trim();
    if (!text) {
      return '';
    }
    if (text.indexOf('_') !== -1) {
      return text.split('_').map(function (word) {
        if (!word) {
          return '';
        }
        return word.charAt(0).toUpperCase() + word.slice(1);
      }).join(' ');
    }
    return this.xmlNameToLabel(text);
  },

  COLLECTION_UI_LABELS: {
    comments: 'Comments',
    identifiers: 'Identifiers',
    operators: 'Operators',
    external_references: 'External References',
    types: 'Types',
    equipments: 'Equipment'
  },

  labelForParameter: function (parameterName, nodeType) {
    var name = String(parameterName || '');
    var collectionLabel = this.COLLECTION_UI_LABELS[name];
    var suffix;
    if (collectionLabel) {
      return collectionLabel;
    }
    suffix = this.xmlSuffixForParameter(name, nodeType);
    if (suffix) {
      return this.xmlNameToLabel(suffix);
    }
    return this.snakeNameToLabel(name);
  },

  labelForRecord: function (record, nodeType) {
    var name;
    var type = nodeType;
    if (!record) {
      return '';
    }
    if (record.get) {
      name = record.get('name') || record.get('id');
      if (type == null) {
        type = record.get('node_type_id');
      }
    } else {
      name = record.name || record.id;
    }
    return this.labelForParameter(name, type);
  },

  ITEM_PARAMETERS: {
    code: 'code',
    start_date: 'start_date',
    end_date: 'end_date',
    latitude: 'latitude',
    longitude: 'longitude',
    elevation: 'elevation',
    location_code: 'location_code',
    depth: 'depth',
    code1: 'code',
    code2: 'code',
    code3: 'code',
    dip1: 'dip',
    dip2: 'dip',
    dip3: 'dip',
    azimuth1: 'azimuth',
    azimuth2: 'azimuth',
    azimuth3: 'azimuth'
  },

  plainLabel: function (value) {
    return String(value == null ? '' : value)
      .replace(/<[^>]*>/g, '')
      .replace(/\s+/g, ' ')
      .trim();
  },

  wizardHelpRequest: function (field) {
    field = field || {};
    var nodeType = field.recordNodeType != null ?
      field.recordNodeType : field.nodeType;
    var parameterName = field.parameterName || field.validationAttr || null;
    var itemId = field.itemId || '';
    var reference = field.reference || '';
    var label = this.plainLabel(field.fieldLabel);

    if (!parameterName && this.ITEM_PARAMETERS[itemId]) {
      parameterName = this.ITEM_PARAMETERS[itemId];
    }
    if (!parameterName && (
      reference === 'askedSampleRate' ||
      /sample rate/i.test(label)
    )) {
      parameterName = 'sample_rate';
    }
    if (!parameterName && (
      reference === 'codePrefix' ||
      label === 'Channel Prefix' ||
      label === 'Channel code'
    )) {
      parameterName = 'code';
    }
    if (!parameterName && label === 'Channel Orientation') {
      parameterName = 'azimuth';
    }
    if (!parameterName && (
      reference === 'orientationApplies' ||
      label === 'Orientation applies'
    )) {
      parameterName = 'dip';
    }
    if (!parameterName) {
      var normalized = label.replace(/:$/, '').trim().toLowerCase();
      parameterName = {
        dip: 'dip',
        azimuth: 'azimuth',
        channel: 'code',
        latitude: 'latitude',
        longitude: 'longitude',
        elevation: 'elevation',
        depth: 'depth',
        'location code': 'location_code',
        'network code': 'code',
        'station code': 'code',
        'start date': 'start_date',
        'end date': 'end_date'
      }[normalized] || null;
    }
    if (!parameterName && field.inSensorModifier) {
      parameterName = 'sensor';
      nodeType = nodeType || 3;
    }
    if (!parameterName && field.inDataloggerModifier) {
      parameterName = 'data_logger';
      nodeType = nodeType || 3;
    }
    if (!parameterName && field.inResponseSelector) {
      parameterName = 'response';
      nodeType = nodeType || 3;
    }

    var search = label;
    if (field.inDataloggerModifier || field.inSensorModifier) {
      search = label.replace(/_/g, ' ');
    } else if (parameterName) {
      search = this.labelForParameter(parameterName, nodeType);
    }

    var levelName = nodeType ? this.nodeTypeName(nodeType) : '';
    var title = search || 'StationXML schema';
    var context;
    if (parameterName) {
      title = (levelName ? this.snakeNameToLabel(levelName) + ' ' : '') +
        (this.labelForParameter(parameterName, nodeType) || search);
      context = {
        nodeType: nodeType,
        parameterName: parameterName,
        search: search
      };
    } else {
      var paths = {
        network: '/FDSNStationXML/Network',
        station: '/FDSNStationXML/Network/Station',
        channel: '/FDSNStationXML/Network/Station/Channel'
      };
      if (levelName) {
        title = this.snakeNameToLabel(levelName);
      }
      context = {
        path: paths[levelName] || '/FDSNStationXML',
        search: search
      };
    }
    return {
      context: context,
      title: title,
      search: search
    };
  },

  searchScore: function (entry, query) {
    var docs = (entry && entry.documentation) || {};
    var haystack = [
      entry && entry.xmlName,
      entry && entry.path,
      entry && entry.declaredType,
      (docs.description || []).join(' ')
    ].join(' ').toLowerCase();
    var compact = haystack.replace(/[^a-z0-9]+/g, '');
    var words = String(query || '').toLowerCase().split(/[^a-z0-9]+/).filter(Boolean);
    if (!entry || !words.length) {
      return 0;
    }
    var matched = 0;
    var i;
    for (i = 0; i < words.length; i++) {
      if (haystack.indexOf(words[i]) !== -1 || compact.indexOf(words[i]) !== -1) {
        matched += 1;
      }
    }
    if (!matched) {
      return 0;
    }
    var score = matched;
    var compactQuery = words.join('');
    if (matched === words.length) {
      score += 10;
    }
    if (compact.indexOf(compactQuery) !== -1) {
      score += 20;
    }
    var xmlName = String(entry.xmlName || '').replace(/^@/, '').toLowerCase();
    if (xmlName === compactQuery) {
      score += 30;
    }
    return score;
  },

  relabelMessages: function (messages, parameterName, nodeType) {
    var name = String(parameterName || '');
    var label;
    if (!name || messages == null) {
      return messages;
    }
    label = this.labelForParameter(name, nodeType);
    if (!label || label === name) {
      return messages;
    }
    return Ext.Array.map(Ext.Array.from(messages), function (msg) {
      return String(msg).split("'" + name + "'").join("'" + label + "'");
    });
  }
});

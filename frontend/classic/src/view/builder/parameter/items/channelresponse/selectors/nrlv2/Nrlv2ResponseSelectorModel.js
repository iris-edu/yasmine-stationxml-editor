/* ****************************************************************************
*
* NRLv2 Response Selector ViewModel - Same structure as NRL
*
* NRLv2 online support (2026): ASGSR, Alexey Emanov.
*
* ****************************************************************************/

Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.nrlv2.Nrlv2ResponseSelectorModel', {
  extend: 'Ext.app.ViewModel',
  alias: 'viewmodel.nrlv2-response-selector',
  data: {
    sensorSelection: null,
    sensorInstconfig: null,
    sensorSource: null,
    sensorPreview: null,
    sensorModelPath: null,
    sensorConfigurations: null,
    sensorParameterNames: [],
    sensorParameterOptions: {},
    sensorModifierValues: {},
    sensorSelectedConfig: null,
    sensorSelectedConfigInfo: '',

    dataloggerSelection: null,
    dataloggerInstconfig: null,
    dataloggerSource: null,
    dataloggerPreview: null,
    dataloggerModelPath: null,
    dataloggerConfigurations: null,
    dataloggerParameterNames: [],
    dataloggerParameterOptions: {},
    dataloggerModifierValues: {},
    dataloggerSelectedConfig: null,
    dataloggerSelectedConfigInfo: '',

    minFrequency: 0.001,
    maxFrequency: null,

    channelResponseImageUrl: null,
    channelResponseCsvUrl: null,
    channelResponseText: null,
    channelResponsePlotMessage: null,

    wizardMode: false,
    responseTree: null,
    activeSelectorTab: 0
  },
  stores: {
    sensorStore: {
      type: 'tree',
      model: 'yasmine.view.xml.builder.parameter.items.channelresponse.nrlv2.Nrlv2ResponseTreeModel',
      proxy: {
        type: 'ajax',
        url: '/api/nrlv2/sensors/',
        timeout: 35000,
        reader: {
          type: 'json',
          rootProperty: 'data'
        }
      },
      autoLoad: false,
      nodeParam: 'node',
      root: {
        id: 0,
        text: '<b>sensor</b>'
      }
    },
    dataloggerStore: {
      type: 'tree',
      model: 'yasmine.view.xml.builder.parameter.items.channelresponse.nrlv2.Nrlv2ResponseTreeModel',
      proxy: {
        type: 'ajax',
        url: '/api/nrlv2/dataloggers/',
        timeout: 35000,
        reader: {
          type: 'json',
          rootProperty: 'data'
        }
      },
      autoLoad: false,
      nodeParam: 'node',
      root: {
        id: 0,
        text: '<b>datalogger</b>'
      }
    },
    dataloggerConfigStore: {
      type: 'store',
      fields: ['instconfig', 'description', 'parameters', 'source'],
      data: []
    }
  },
  formulas: {
    dataloggerStatus: function (get) {
      return get('dataloggerPreview')
        ? ' <i class="fa fa-check" style="color: green"></i>'
        : ' <i class="fa fa-ban" style="color: red"></i>';
    },
    sensorStatus: function (get) {
      return get('sensorPreview')
        ? ' <i class="fa fa-check" style="color: green"></i>'
        : ' <i class="fa fa-ban" style="color: red"></i>';
    },
    responseStatus: function (get) {
      return (get('sensorPreview') && get('dataloggerPreview'))
        ? ' <i class="fa fa-check" style="color: green"></i>'
        : ' <i class="fa fa-ban" style="color: red"></i>';
    },
    responsePreviewWizardCls: function (get) {
      return get('wizardMode') ? 'response-preview-wizard' : '';
    },
    instconfig: function (get) {
      let s = get('sensorInstconfig');
      let d = get('dataloggerInstconfig');
      return (s && d) ? s + ':' + d : null;
    },
    dataloggerFilteredConfigs: function (get) {
      let configs = get('dataloggerConfigurations') || [];
      let modifierValues = get('dataloggerModifierValues') || {};
      let paramNames = get('dataloggerParameterNames') || [];
      if (!paramNames.length) return configs;
      return configs.filter(function (c) {
        let params = c.parameters || {};
        for (let i = 0; i < paramNames.length; i++) {
          let pname = paramNames[i];
          let sel = modifierValues[pname];
          if (sel && sel !== '*') {
            if (String(params[pname] || '').trim() !== String(sel).trim()) {
              return false;
            }
          }
        }
        return true;
      });
    },
    dataloggerFilteredCount: function (get) {
      return (get('dataloggerFilteredConfigs') || []).length;
    },
    dataloggerConfigCountText: function (get) {
      let n = get('dataloggerFilteredCount') || 0;
      return n + ' configuration(s)';
    },
    dataloggerConfigListText: function (get) {
      let configs = get('dataloggerFilteredConfigs') || [];
      if (configs.length <= 1) return '';
      return configs.map(function (c) {
        return c.description || c.instconfig || '';
      }).join('\n');
    },
    sensorFilteredConfigs: function (get) {
      let configs = get('sensorConfigurations') || [];
      let modifierValues = get('sensorModifierValues') || {};
      let paramNames = get('sensorParameterNames') || [];
      if (!paramNames.length) return configs;
      return configs.filter(function (c) {
        let params = c.parameters || {};
        for (let i = 0; i < paramNames.length; i++) {
          let pname = paramNames[i];
          let sel = modifierValues[pname];
          if (sel && sel !== '*') {
            if (String(params[pname] || '').trim() !== String(sel).trim()) {
              return false;
            }
          }
        }
        return true;
      });
    },
    sensorFilteredCount: function (get) {
      return (get('sensorFilteredConfigs') || []).length;
    },
    sensorConfigCountText: function (get) {
      let n = get('sensorFilteredCount') || 0;
      return n + ' configuration(s)';
    },
    sensorPreviewWithConfigInfo: function (get) {
      let preview = get('sensorPreview') || '';
      let selectedInfo = (get('sensorSelectedConfigInfo') || '').trim();
      if (!selectedInfo) {
        return preview;
      }
      let output = [selectedInfo];
      if (!preview) {
        return output.join('\n');
      }
      return output.join('\n') + '\n\n' + preview;
    },
    dataloggerPreviewWithConfigInfo: function (get) {
      let preview = get('dataloggerPreview') || '';
      let selectedInfo = (get('dataloggerSelectedConfigInfo') || '').trim();
      if (!selectedInfo) {
        return preview;
      }
      let output = [selectedInfo];
      if (!preview) {
        return output.join('\n');
      }

      let lines = String(preview).split('\n');
      let stageBlocks = [];
      let generalLines = [];
      let currentStage = null;

      let shouldSkip = function (line) {
        let l = String(line || '').toLowerCase();
        return l.indexOf('numerator coefficients') >= 0 ||
          l.indexOf('denominator coefficients') >= 0 ||
          l.indexOf('fir coefficients') >= 0 ||
          l.indexOf('coefficients:') >= 0;
      };

      let keepStageLine = function (line) {
        return /stage gain|input units|output units|input sample rate|output sample rate|decimation factor|decimation offset|delay|correction|normalization factor|normalization frequency|number of zeros|number of poles|transfer function/i
          .test(line);
      };

      lines.forEach(function (lineRaw) {
        let line = String(lineRaw || '').trim();
        if (!line) return;
        if (shouldSkip(line)) return;

        let stageMatch = line.match(/^Stage\s+\d+\s*:/i);
        if (stageMatch) {
          currentStage = { header: line, details: [] };
          stageBlocks.push(currentStage);
          return;
        }

        if (currentStage) {
          if (keepStageLine(line)) {
            currentStage.details.push(line);
          }
        } else {
          if (/channel response|overall sensitivity|\dstages?:|from .* to /i.test(line)) {
            generalLines.push(line);
          }
        }
      });

      output.push('Channel Response (stage details):');
      generalLines.forEach(function (line) {
        output.push(line);
      });
      stageBlocks.forEach(function (st) {
        output.push(st.header);
        st.details.forEach(function (d) {
          output.push('  ' + d);
        });
      });
      return output.join('\n');
    }
  }
});


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.nrlv2.Nrlv2ResponseTreeModel', {
  extend: 'Ext.data.TreeModel',
  fields: [
    { name: 'text', type: 'string', persist: false },
    { name: 'key', type: 'string', persist: false },
    { name: 'leaf', type: 'boolean', persist: false },
    { name: 'source', type: 'string', persist: false },
    {
      name: 'title',
      type: 'string',
      persist: false,
      convert: function (value, record) {
        let delimiter = record.get('key') ? ':' : '';
        let text = (record.get('text') || '').replace('Select the', '').trim();
        if (!text) {
          text = '';
          delimiter = '';
        }
        return `<b>${text}${delimiter}</b> ${record.get('key') || ''}`;
      }
    }
  ]
});

/* ****************************************************************************
* 2026-09-25, version 4.3.3-beta: ASGSR, Alexey Emanov
*
* This file is part of the yasmine editing tool.
*
* yasmine (Yet Another Station Metadata INformation Editor), a tool to
* create and edit station metadata information in FDSN stationXML format,
* is a common development of IRIS and RESIF.
* Development and addition of new features is shared and agreed between * IRIS and RESIF.
*
*
* Version 1.0 of the software was funded by SAGE, a major facility fully
* funded by the National Science Foundation (EAR-1261681-SAGE),
* development done by ISTI and led by IRIS Data Services.
* Version 2.0 of the software was funded by CNRS and development led by * RESIF.
*
* NRLv2 online support (2026): ASGSR, Alexey Emanov.
*
* This program is free software; you can redistribute it
* and/or modify it under the terms of the GNU Lesser General Public
* License as published by the Free Software Foundation; either
* version 3 of the License, or (at your option) any later version. *
* This program is distributed in the hope that it will be
* useful, but WITHOUT ANY WARRANTY; without even the implied warranty
* of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
* GNU Lesser General Public License (GNU-LGPL) for more details. *
* You should have received a copy of the GNU Lesser General Public
* License along with this software. If not, see
* <https://www.gnu.org/licenses/>
*
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.wizard.channelsteps.steps.Step3View', {
  extend: 'Ext.panel.Panel',
  xtype: 'channel-step-3',
  requires: [
    'yasmine.view.xml.builder.parameter.items.channelresponse.nrl.NrlResponseSelector',
    'yasmine.view.xml.builder.parameter.items.channelresponse.arol.ArolResponseSelector',
    'yasmine.view.xml.builder.parameter.items.channelresponse.nrlv2.Nrlv2ResponseSelector'
  ],
  controller: {
    selector: null,
    isValid: function () {
      let stepsData = this.getViewModel().get('stepsStoredData');
      if (stepsData.selectedLibrary !== 'none') {
        let cmpController = this.selector.getController();
        let responseType = stepsData.nrlResponseType;
        if (responseType === 'integrated' || responseType === 'soh') {
          if (!cmpController.isDataloggerCompleted || !cmpController.isDataloggerCompleted()) {
            Ext.Msg.alert('Error', 'Please complete the selection', Ext.emptyFn);
            return false;
          }
          return true;
        }
        if (!cmpController.isDataloggerCompleted || !cmpController.isDataloggerCompleted()) {
          Ext.Msg.alert('Error', 'Please complete datalogger selection', Ext.emptyFn);
          return false;
        }
        if (!cmpController.isSensorCompleted || !cmpController.isSensorCompleted()) {
          Ext.Msg.alert('Error', 'Please complete sensor selection', Ext.emptyFn);
          return false;
        }
        return true;
      }
      return true;
    },
    storeStepData: function () {
      let viewModel = this.getViewModel();
      let stepsData = viewModel.get('stepsStoredData');
      let cmpController = this.selector.getController();
      stepsData.dataloggerKeys = [];
      stepsData.sensorKeys = [];
      stepsData.instconfig = null;
      stepsData.sohChannelDescription = null;
      stepsData.sohSampleRate = null;
      stepsData.sensorType = null;
      stepsData.angularPeriod = null;
      stepsData.sampleRate = null;
      stepsData.configDescription = null;
      stepsData.inputUnits = null;
      if (stepsData.selectedLibrary === 'nrlv2_online') {
        let selectorModel = cmpController.getViewModel();
        stepsData.instconfig = selectorModel.get('instconfig');
        let sensorSource = selectorModel.get('sensorSource');
        let dataloggerSource = selectorModel.get('dataloggerSource');
        stepsData.source = (sensorSource && sensorSource === dataloggerSource)
          ? sensorSource
          : (sensorSource || dataloggerSource || null);
        let sensorConfig = selectorModel.get('sensorSelectedConfig') || {};
        let loggerConfig = selectorModel.get('dataloggerSelectedConfig') || {};
        let sensorParams = sensorConfig.parameters || {};
        let loggerParams = loggerConfig.parameters || {};
        if (stepsData.nrlResponseType === 'soh') {
          stepsData.sohChannelDescription = loggerParams.Channel_Description || null;
          stepsData.sohSampleRate = loggerParams.Final_Sample_Rate || null;
        } else {
          stepsData.sensorType = sensorParams.Sensor_Type || loggerParams.Sensor_Type || null;
          stepsData.angularPeriod = this.angularPeriodFromParams(sensorParams)
            || this.angularPeriodFromParams(loggerParams);
          stepsData.sampleRate = loggerParams.Final_Sample_Rate || sensorParams.Final_Sample_Rate || null;
          stepsData.configDescription = [sensorConfig.description, loggerConfig.description]
            .filter(Boolean).join(' ');
          stepsData.inputUnits = this.inputUnitsFromText(
            stepsData.nrlResponseType === 'integrated'
              ? (selectorModel.get('dataloggerPreview') || selectorModel.get('channelResponseText'))
              : (selectorModel.get('sensorPreview') || selectorModel.get('channelResponseText'))
          );
        }
      } else if (stepsData.selectedLibrary !== 'none') {
        stepsData.dataloggerKeys = cmpController.getSelectedDataloggerKeys();
        stepsData.sensorKeys = cmpController.getSelectedSensorKeys();
        let selectorModel = cmpController.getViewModel();
        let preview = stepsData.nrlResponseType === 'integrated'
          ? selectorModel.get('dataloggerPreview')
          : selectorModel.get('sensorPreview');
        stepsData.inputUnits = this.inputUnitsFromText(preview);
      }
      let channelInfo = viewModel.get('channelInfo');
      channelInfo.set('sensorKeys', stepsData.sensorKeys);
      channelInfo.set('dataloggerKeys', stepsData.dataloggerKeys);
      channelInfo.set('instconfig', stepsData.instconfig);
      channelInfo.set('source', stepsData.source || null);
      channelInfo.set('nrlResponseType', stepsData.nrlResponseType || null);
      if (stepsData.selectedLibrary !== 'none' && this.selector && this.selector.getViewModel) {
        channelInfo.set('responseTree', cmpController.getViewModel().get('responseTree') || null);
      } else {
        channelInfo.set('responseTree', null);
      }
    },
    angularPeriodFromParams: function (params) {
      let source = params || {};
      let keys = [
        'Long-Period_Corner',
        'Short-Period_Corner',
        'Low-Frequency_Corner',
        'Low-Frequency Corner'
      ];
      for (let i = 0; i < keys.length; i++) {
        if (source[keys[i]]) {
          return source[keys[i]];
        }
      }
      return null;
    },
    inputUnitsFromText: function (text) {
      let source = String(text || '');
      let resp = source.match(/B054F05[^\n]*:\s*([^\n]+)/);
      if (resp) {
        return resp[1].split(' - ')[0].trim() || null;
      }
      let stage = source.match(/\bfrom\s+(\S+)\s+to\s+/i);
      if (stage) {
        return stage[1];
      }
      let header = source.match(/\bFrom\s+(\S+)\s+\(/);
      if (header) {
        return header[1];
      }
      return null;
    },
    recalculateSensitivity: function () {
      if (this.selector && this.selector.getController) {
        let ctrl = this.selector.getController();
        if (ctrl && typeof ctrl.recalculateSensitivity === 'function') {
          ctrl.recalculateSensitivity();
        }
      }
    },
    initComponent: function () {
      let container = this.getView();
      container.removeAll(true, true);

      let stepsData = this.getViewModel().get('stepsStoredData');
      let responseType = stepsData.nrlResponseType;
      let responseElement = (responseType === 'integrated' || responseType === 'soh') ? responseType : null;
      if (stepsData.selectedLibrary === 'none') {
        this.selector = Ext.create({
          xtype: 'panel',
          html: '<div style="width: 100%; position: relative; top: 50%; text-align: center; font-size: 14px; font-weight: bold;">Creation of a response is skipped, please click "Next" to proceed further.</div>'
        });
      } else if (stepsData.selectedLibrary === 'nrlv2_online') {
        this.selector = Ext.create({
          xtype: 'nrlv2-response-selector',
          responseElement: responseElement,
          style: 'border: solid #d0d0d0 1px;'
        });
      } else if (stepsData.selectedLibrary === 'arol') {
        this.selector = Ext.create({
          xtype: 'arol-response-selector',
          style: 'border: solid #d0d0d0 1px;'
        });
      } else if (stepsData.selectedLibrary === 'nrl') {
        this.selector = Ext.create({
          xtype: 'nrl-response-selector',
          responseElement: responseElement
        });
      }

      container.add(this.selector);
      if (this.selector && this.selector.getViewModel && stepsData.selectedLibrary !== 'none') {
        this.selector.getViewModel().set('wizardMode', true);
      }
    }
  }
});

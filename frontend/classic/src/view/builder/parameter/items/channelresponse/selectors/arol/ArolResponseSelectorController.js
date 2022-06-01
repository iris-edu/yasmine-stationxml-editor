/* ****************************************************************************
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


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.arolselector.ArolResponseSelectorController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.arol-response-selector',
  init: function () {
    this.loadDataloggerKeys();
    this.loadSensorKeys();
  },
  fillRecord: function () {
    let dataloggerCompleted = this.getViewModel().get('dataloggerCompleted');
    let sensorCompleted = this.getViewModel().get('sensorCompleted');
    if (!dataloggerCompleted || !sensorCompleted) {
      return;
    }

    let record = this.getViewModel().get('record');
    let sensorKeys = this.getViewModel().get('sensor').selectedFiles;
    let dataloggerKeys = this.getViewModel().get('datalogger').selectedFiles;
    record.set('value', {libraryType: 'arol', sensorKeys, dataloggerKeys});
  },
  onDataloggerFilterOptionChange: function (cmp, newValue, oldValue) {
    let selectedOptions = this.getViewModel().get('datalogger.selectedOptions');
    let newSelectedOptions = this.updateSelectedOptions(selectedOptions, newValue, oldValue, 'datalogger');
    this.setViewModelValue('datalogger', 'selectedOptions', newSelectedOptions);
    this.updateDataloggerView();
    this.checkDataloggerCompleteness();
    this.loadInstrumentPreviewIfPossible('datalogger');
  },
  onSensorFilterOptionChange: function (cmp, newValue, oldValue) {
    let selectedOptions = this.getViewModel().get('sensor.selectedOptions');
    let newSelectedOptions = this.updateSelectedOptions(selectedOptions, newValue, oldValue, 'sensor');
    this.setViewModelValue('sensor', 'selectedOptions', newSelectedOptions);
    this.updateSensorView();
    this.checkSensorCompleteness();
    this.loadInstrumentPreviewIfPossible('sensor');
  },
  loadChannelResponsePlot: function () {
    this.loadChannelResponseIfPossible();
  },
  downloadChannelResponsePlot: function () {
    let win = window.open('', '_blank');
    win.location = this.getViewModel().get('channelResponseImageUrl');
    win.focus();
  },
  downloadChannelResponseCsv: function () {
    let win = window.open('', '_self');
    win.location = this.getViewModel().get('channelResponseCsvUrl');
    win.focus();
  },
  updateDataloggerView: function () {
    let data = this.getDataloggerJson();
    let selectedOptions = this.getViewModel().get('datalogger.selectedOptions');
    this.updateCheckboxes(data, 'datalogger', 'onDataloggerFilterOptionChange');
    this.updateResponseList(data, 'datalogger', this.lookupReference('datalogger_response'), selectedOptions);
  },
  updateSensorView: function () {
    let data = this.getSensorJson();
    let selectedOptions = this.getViewModel().get('sensor.selectedOptions');
    this.updateCheckboxes(data, 'sensor', 'onSensorFilterOptionChange');
    this.updateResponseList(data, 'sensor', this.lookupReference('sensor_response'), selectedOptions);
  },
  updateSelectedOptions: function (selectedOptions, newValue, oldValue, instrument) {
    let oldOption = new Map(Object.entries(oldValue));
    for (let key of oldOption.keys()) {
      selectedOptions.delete(key);
    }
    let keyData = instrument === 'datalogger' ? this.getDataloggerJson() : this.getSensorJson()
    let required = keyData.filters.filter(x => x.required).map(x => x.code);
    let clean = false;
    for (let key of required) {
      if (oldValue.hasOwnProperty(key)) {
        clean = true;
        break;
      }
    }
    if (clean) {
      for (let key of [... required].reverse()) {
        if (!oldValue.hasOwnProperty(key)) {
          required.pop();
        }
      }
      for (let key of Array.from(selectedOptions.keys()).reverse()) {
        if (!required.includes(key)) {
          selectedOptions.delete(key);
        }
      }
    }
    return new Map([...selectedOptions, ...new Map(Object.entries(newValue))]);
  },
  updateCheckboxes: function (data, instrument, handlerName) {
    let selectedOptions = this.getViewModel().get(instrument).selectedOptions;
    let availableFilters = this.getAvailableFilters(data, selectedOptions);
    let currentFilteredFiles = this.getFilteredFiles(data, selectedOptions).join('');
    for (const [key, value] of availableFilters.entries()) {
      if (selectedOptions.has(key)) {
        availableFilters.set(key, [selectedOptions.get(key)]);
        continue;
      }
      let newValues = [];
      for (const filterValue of value) {
        let newSelectedOptions = new Map(selectedOptions);
        newSelectedOptions.set(key, filterValue);
        let newFilteredFiles = this.getFilteredFiles(data, newSelectedOptions).join('');
        if (currentFilteredFiles !== newFilteredFiles) {
          newValues.push(filterValue);
        }
      }
      availableFilters.set(key, newValues);
    }

    let container = this.lookupReference(instrument);
    container.removeAll(false);

    let availableFilterGroups = 0;
    let priorityFilters = data.filters.filter(x => x.required && !this.isGroupSelected(x.code, availableFilters))
    data.filters.forEach(filter => {
      if (!availableFilters.has(filter.code)) {
        return;
      }

      let options = availableFilters.get(filter.code);
      if (options.length === 0) {
        return;
      }

      let checkboxes = options.map(option => {
        return {
          boxLabel: option,
          inputValue: option,
          checked: selectedOptions.has(filter.code) && selectedOptions.get(filter.code) === option
        }
      });

      let name = filter.required ? `* ${filter.name}` : filter.name;
      let fieldset = Ext.create({
        xtype: 'fieldset',
        disabled: !filter.required && priorityFilters.length > 0,
        title: `${name} <i class="fa fa-question-circle" data-qtip="${filter.help}"></i>`,
        items: Ext.create({
          xtype: 'checkboxgroup',
          columns: 1,
          name: filter.code,
          items: checkboxes,
          listeners: {
            'change': handlerName
          }
        })
      });

      if (checkboxes.length > 1 || (checkboxes.length === 1 && checkboxes[0].checked)) {
        container.add(fieldset);
        availableFilterGroups++;
      }
    });

    this.getViewModel().get(instrument).availableFilterGroups = availableFilterGroups;
  },
  isGroupSelected: function (groupName, availableFilters) {
    return availableFilters.has(groupName)
      && (availableFilters.get(groupName).length === 1 || availableFilters.get(groupName).length === 0);
  },
  updateResponseList: function (data, instrument, container, selectedOptions) {
    let files = this.getFilteredFiles(data, selectedOptions);

    let filesHtml = files.map(x => `<a  href="#">${x}</a>`).join('<br/>');

    let response = new Map();
    files.forEach(path => {
      let filterObject = data.responses.find(x => x.path === path).applicable_filters;
      for (let [key, value] of Object.entries(filterObject)) {
        if (!response.has(key)) {
          response.set(key, new Set());
        }
        if (value) {
          response.get(key).add(value);
        }
      }
    });

    let values = [];
    for (let [key, value] of response.entries()) {
      if (value.size > 1) {
        values = [];
        break;
      }

      let title = value.values().next().value;
      if (title !== 'NaN') {
        values.push(title);
      }
    }

    container.setHtml(filesHtml);

    this.getViewModel().get(instrument).resultTitle = values.filter(x => x).join(', ');
    this.getViewModel().get(instrument).selectedFiles = [...files];
    this.getViewModel().set('sensor_file', '');
    this.getViewModel().set('datalogger_file', '');
  },
  getFilteredFiles: function (data, selectedOptions) {
    const allResponses = data.responses;
    let files = allResponses.map(x => x.path);

    if (selectedOptions.size > 0) {
      files = [];
      for (let response of allResponses) {
        let filter = response.applicable_filters;
        let matchedFilters = 0;
        for (let key of selectedOptions.keys()) {
          if (filter.hasOwnProperty(key) && (filter[key] === selectedOptions.get(key) || filter[key] === null)) {
            matchedFilters++;
          }
        }
        if (matchedFilters === selectedOptions.size) {
          files.push(response.path);
        }
      }
    }

    let collator = new Intl.Collator(undefined, {numeric: true, sensitivity: 'base'});
    return Array.from(new Set(files)).sort(collator.compare);
  },
  getAvailableFilters: function (data, selectedOptions) {
    let applicableFilters = data.responses.map(x => x.applicable_filters);
    if (selectedOptions.size > 0) {
      applicableFilters = applicableFilters.filter(response => {
        let matchedFilters = 0;
        for (let [key, value] of selectedOptions.entries()) {
          let availableOption = response[key];
          if (availableOption === value || availableOption === null) {
            matchedFilters++;
          }
        }
        return selectedOptions.size === matchedFilters;
      });
    }

    let filterMap = new Map();
    applicableFilters.forEach(filterObject => {
      for (let [key, value] of Object.entries(filterObject)) {
        if (!filterMap.has(key)) {
          filterMap.set(key, new Set());
        }
        if (selectedOptions.has(key)) {
          filterMap.get(key).add(selectedOptions.get(key));
        } else if (value) {
          filterMap.get(key).add(value);
        }
      }
    });

    let collator = new Intl.Collator(undefined, {numeric: true, sensitivity: 'base'});
    for (const [key, value] of filterMap.entries()) {
      filterMap.set(key, Array.from(value).sort(collator.compare));
    }

    return filterMap;
  },
  onSensorFileClick: function (e, ref) {
    e.preventDefault();
    this.getViewModel().set('sensor_file', this.findFilter(this.getSensorJson(), ref.text));
  },
  onDataloggerFileClick: function (e, ref) {
    e.preventDefault();
    this.getViewModel().set('datalogger_file', this.findFilter(this.getDataloggerJson(), ref.text));
  },
  findFilter: function (data, path) {
    if (!path) {
      return '';
    }
    let result = `<b>${path}</b> <br/>`;
    let filters = data.responses.find(x => x.path === path).applicable_filters;
    for (let filter of Array.from(new Map(Object.entries(filters)).keys()).sort()) {
      result += `${filter}:<i style="position: absolute; left: 200px;">${filters[filter] ? filters[filter] : '<span style="color: red">any</span>'}</i> <br/>`
    }
    return result;
  },
  getFilterOptions: function (filterCode, data, selectedOptions) {
    let responses = data.responses;
    let applicableFilters = responses.map(x => x.applicable_filters);
    if (selectedOptions.size > 0) {
      let filters = [];
      for (let applicableFilter of applicableFilters) {
        let matchedFilters = 0;
        for (let key of selectedOptions.keys()) {
          if (applicableFilter.hasOwnProperty(key) && (applicableFilter[key] === selectedOptions.get(key) || applicableFilter[key] === null)) {
            matchedFilters++;
          }
        }
        if (matchedFilters === selectedOptions.size) {
          filters.push(applicableFilter);
        }
      }
      applicableFilters = filters;
    }

    let allOptions = applicableFilters
      .map(y => y[filterCode])
      .filter(x => x);

    let collator = new Intl.Collator(undefined, {numeric: true, sensitivity: 'base'});
    return Array.from(new Set(allOptions)).sort(collator.compare);
  },
  loadDataloggerKeys: function () {
    let that = this;
    Ext.Ajax.request({
      method: 'GET',
      url: `/api/arol/datalogger/key`,
      success: function (response) {
        that.setViewModelValue('datalogger', 'keys', JSON.parse(response.responseText));
        that.updateDataloggerView();
      }
    });
  },
  loadSensorKeys: function () {
    let that = this;
    Ext.Ajax.request({
      method: 'GET',
      url: `/api/arol/sensor/key`,
      success: function (response) {
        that.setViewModelValue('sensor', 'keys', JSON.parse(response.responseText));
        that.updateSensorView();
      }
    });
  },
  checkDataloggerCompleteness: function () {
    let isCompleted = this.getViewModel().get('datalogger').selectedOptions.size === this.getViewModel().get('datalogger').availableFilterGroups;
    this.getViewModel().set('dataloggerCompleted', isCompleted);
    this.loadChannelResponseIfPossible();
  },
  checkSensorCompleteness: function () {
    let isCompleted = this.getViewModel().get('sensor').selectedOptions.size === this.getViewModel().get('sensor').availableFilterGroups;
    this.getViewModel().set('sensorCompleted', isCompleted);
    this.loadChannelResponseIfPossible();
  },
  getSelectedSensorKeys: function () {
    let selectedOptions = this.getViewModel().get('sensor').selectedOptions.size;
    if (selectedOptions === 0) {
      return [];
    }
    return [...this.getViewModel().get('sensor').selectedFiles];
  },
  isDataloggerCompleted: function () {
    return this.getViewModel().get('dataloggerCompleted');
  },
  isSensorCompleted: function () {
    return this.getViewModel().get('sensorCompleted');
  },
  getSelectedDataloggerKeys: function () {
    let selectedOptions = this.getViewModel().get('datalogger').selectedOptions.size;
    if (selectedOptions === 0) {
      return [];
    }
    return [...this.getViewModel().get('datalogger').selectedFiles];
  },
  loadChannelResponseIfPossible: function () {
    if (!this.getViewModel().get('sensorCompleted') || !this.getViewModel().get('dataloggerCompleted')) {
      Ext.ux.Mediator.fireEvent('parameterEditorController-canSaveButton', false);
      return;
    }

    let min = this.getViewModel().get('minFrequency');
    let max = this.getViewModel().get('maxFrequency');
    let sensorKeys = this.getViewModel().get('sensor').selectedFiles;
    let dataloggerKeys = this.getViewModel().get('datalogger').selectedFiles;
    let that = this;
    that.getViewModel().set('channelResponseText', null);
    Ext.Ajax.request({
      method: 'GET',
      params: {sensorKeys, dataloggerKeys, min, max},
      url: '/api/arol/channel/response/preview/',
      success: function (response) {
        let result = JSON.parse(response.responseText);
        if (result.text) {
          that.getViewModel().set('channelResponseText', result.text);
          Ext.ux.Mediator.fireEvent('parameterEditorController-canSaveButton', true);
        }
        if (result.plot_url) {
          that.getViewModel().set('channelResponseImageUrl', result.plot_url);
        }
        if (result.csv_url) {
          that.getViewModel().set('channelResponseCsvUrl', result.csv_url);
        }
        if (!result.success || result.message) {
          that.getViewModel().set('channelResponseImageUrl', null);
          Ext.MessageBox.show({
            title: 'An error occurred',
            msg: result.message,
            buttons: Ext.MessageBox.OK,
            icon: Ext.MessageBox['ERROR']
          });
        }
      }
    });
  },
  loadInstrumentPreviewIfPossible: function (device) {
    this.getViewModel().set(`${device}Preview`, '');
    if (!this.getViewModel().get(`${device}Completed`)) {
      return;
    }
    let that = this;
    let keys = this.getViewModel().get(device).selectedFiles;
    Ext.Ajax.request({
      method: 'GET',
      params: {keys},
      url: `/api/arol/${device}/response/`,
      success: function (response, options) {
        that.getViewModel().set(`${device}Preview`, response.responseText);
      }
    });
  },
  setViewModelValue: function (instrument, property, value) {
    this.getViewModel().get(instrument)[property] = value;
  },
  getSensorJson: function () {
    return this.getViewModel().get('sensor.keys');
  },
  getDataloggerJson: function () {
    return this.getViewModel().get('datalogger.keys');
  }
});

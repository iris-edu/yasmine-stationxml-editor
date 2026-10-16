/* ****************************************************************************
*
* This file is part of the yasmine editing tool.
*
* yasmine (Yet Another Station Metadata INformation Editor), a tool to
* create and edit station metadata information in FDSN stationXML format,
* is a common development of IRIS and RESIF.
* Development and addition of new features is shared and agreed between * IRIS and RESIF.
*
* Version 1.0 of the software was funded by SAGE, a major facility fully
* funded by the National Science Foundation (EAR-1261681-SAGE),
* development done by ISTI and led by IRIS Data Services.
* Version 2.0 of the software was funded by CNRS and development led by * RESIF.
*
* This program is free software; you can redistribute it
* and/or modify it under the terms of the GNU Lesser General Public
* License as published by the Free Software Foundation; either
* version 3 of the License, or (at your option) any later version.
*
* This program is distributed in the hope that it will be
* useful, but WITHOUT ANY WARRANTY; without even the implied warranty
* of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
* GNU Lesser General Public License (GNU-LGPL) for more details.
*
* You should have received a copy of the GNU Lesser General Public
* License along with this software. If not, see
* <https://www.gnu.org/licenses/>
*
*
* 2019/10/07 : version 2.0.0 initial commit
* 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.parameter.items.dataavailability.DataAvailabilityEditorController', {
  extend: 'yasmine.view.xml.builder.parameter.ParameterItemEditorController',
  alias: 'controller.data-availability-editor',

  parseDate: function (value) {
    var normalized;
    var state;
    var ns;
    var millis;

    // ObsPy / jsonpickle may emit false for missing UTCDateTime fields.
    if (value == null || value === false || value === '') {
      return null;
    }
    if (Ext.isDate(value)) {
      return value;
    }
    // Nested UTCDateTime from jsonpickle when the backend did not stringify it:
    // { "py/object": "...UTCDateTime", "py/state": { "py/tuple": [nanoseconds, precision] } }
    if (Ext.isObject(value) && value['py/object'] &&
        String(value['py/object']).indexOf('UTCDateTime') >= 0) {
      state = value['py/state'];
      ns = state && (Ext.isArray(state['py/tuple']) ? state['py/tuple'][0] :
        (Ext.isArray(state) ? state[0] : null));
      if (typeof ns === 'number') {
        millis = ns / 1e6;
        return isFinite(millis) ? new Date(millis) : null;
      }
      return null;
    }
    if (typeof value !== 'string' && typeof value !== 'number') {
      return null;
    }
    normalized = String(value).replace('T', ' ').replace(/Z$/, '').replace(/\.\d+$/, '');
    return Ext.Date.parse(normalized, yasmine.Globals.DateReadFormat, true) ||
      Ext.Date.parse(normalized, yasmine.Globals.DatePrintLongFormat, true) ||
      Ext.Date.parse(normalized, 'Y-m-d H:i:s', true);
  },

  formatDate: function (value) {
    return value ? Ext.Date.format(value, 'Y-m-d\\TH:i:s\\Z') : null;
  },

  spanNumberSegments: function (span) {
    if (span.numberSegments != null) {
      return span.numberSegments;
    }
    if (span.number_of_segments != null) {
      return span.number_of_segments;
    }
    return span.number_segments;
  },

  spanMaximumTimeTear: function (span) {
    if (span.maximumTimeTear != null) {
      return span.maximumTimeTear;
    }
    return span.maximum_time_tear;
  },

  initData: function () {
    var record = this.getViewModel().get('record');
    var value = record.get('value') || {};
    // API / ObsPy shape: { start, end, spans }. Editor / fillRecord shape: { extent, spans }.
    var hasExtentObject = value.extent != null && Ext.isObject(value.extent);
    var extent = hasExtentObject ? value.extent : {
      start: value.start,
      end: value.end
    };
    var spans = value.spans || [];
    var store = this.getViewModel().getStore('spanStore');
    var fieldset = this.lookupReference('extentFieldset');
    var me = this;
    var extentStart;
    var extentEnd;

    if (!Ext.isArray(spans) && spans) {
      spans = [spans];
    }

    store.removeAll();
    extentStart = this.parseDate(extent.start);
    extentEnd = this.parseDate(extent.end);
    this.getViewModel().set({
      extentStart: extentStart,
      extentEnd: extentEnd
    });

    Ext.Array.each(spans, function (span) {
      store.add({
        start: me.parseDate(span.start),
        end: me.parseDate(span.end),
        numberSegments: me.spanNumberSegments(span),
        maximumTimeTear: me.spanMaximumTimeTear(span)
      });
    });

    if (extentStart || extentEnd) {
      fieldset.expand();
    } else {
      fieldset.collapse();
    }
  },

  fillRecord: function () {
    var viewModel = this.getViewModel();
    var fieldset = this.lookupReference('extentFieldset');
    var includeExtent = !fieldset.collapsed;
    var me = this;
    var spans = [];
    var extentStart = includeExtent ? this.formatDate(viewModel.get('extentStart')) : null;
    var extentEnd = includeExtent ? this.formatDate(viewModel.get('extentEnd')) : null;

    viewModel.getStore('spanStore').each(function (span) {
      var numberSegments = span.get('numberSegments');
      var maximumTimeTear = span.get('maximumTimeTear');
      spans.push({
        start: me.formatDate(span.get('start')),
        end: me.formatDate(span.get('end')),
        // Editor / StationXML camelCase
        numberSegments: numberSegments,
        maximumTimeTear: maximumTimeTear,
        // Backend / ObsPy snake_case expected by _update_data_availability
        number_of_segments: numberSegments,
        maximum_time_tear: maximumTimeTear
      });
    });

    viewModel.get('record').set('value', {
      // Backend DataAvailability uses top-level start/end for Extent
      start: extentStart,
      end: extentEnd,
      // Keep nested extent for in-memory round-trip through initData
      extent: includeExtent ? {
        start: extentStart,
        end: extentEnd
      } : null,
      spans: spans
    });
  },

  validate: function () {
    var errors = [];
    var fieldset = this.lookupReference('extentFieldset');
    var viewModel = this.getViewModel();

    if (!fieldset.collapsed &&
        (!viewModel.get('extentStart') || !viewModel.get('extentEnd'))) {
      errors.push('Extent start and end are both required when an extent is included.');
    }

    viewModel.getStore('spanStore').each(function (span, index) {
      if (!span.get('start') || !span.get('end') ||
          span.get('numberSegments') == null ||
          span.get('numberSegments') === '') {
        errors.push('Span ' + (index + 1) +
          ' requires start, end, and number of segments.');
      }
    });

    viewModel.set('validation.activeErrors', errors);
    if (errors.length) {
      return false;
    }
    return this.callParent(arguments);
  },

  onAddSpanClick: function () {
    var store = this.getViewModel().getStore('spanStore');
    var span = new yasmine.view.xml.builder.parameter.items.dataavailability.DataAvailabilitySpan();
    var grid = this.lookupReference('spanGrid');

    store.add(span);
    grid.findPlugin('rowediting').startEdit(span, 0);
  },

  onDeleteSpanClick: function () {
    this.getViewModel().getStore('spanStore').remove(
      this.getViewModel().get('selectedSpan')
    );
  },

  onCancelSpanEditing: function (editor, context) {
    if (context.record.phantom) {
      this.getViewModel().getStore('spanStore').remove(context.record);
    }
  }
});

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
* 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.parameter.items.measurement.MeasurementMetadata', {
  singleton: true,

  definitions: {
    latitude: {
      label: 'Latitude',
      fixedUnit: 'DEGREES',
      hasDatum: true,
      defaultDatum: 'WGS84'
    },
    longitude: {
      label: 'Longitude',
      fixedUnit: 'DEGREES',
      hasDatum: true,
      defaultDatum: 'WGS84'
    },
    elevation: {
      label: 'Elevation',
      defaultUnit: 'METERS'
    },
    depth: {
      label: 'Depth',
      defaultUnit: 'METERS'
    },
    azimuth: {
      label: 'Azimuth',
      fixedUnit: 'DEGREES'
    },
    dip: {
      label: 'Dip',
      fixedUnit: 'DEGREES'
    },
    water_level: {
      label: 'Water Level'
    },
    sample_rate: {
      label: 'Sample Rate',
      fixedUnit: 'HERTZ'
    },
    clock_drift: {
      label: 'Clock Drift',
      fixedUnit: 'SECONDS/SAMPLE'
    },
    clock_drift_in_seconds_per_sample: {
      label: 'Clock Drift',
      fixedUnit: 'SECONDS/SAMPLE'
    }
  },

  getDefinition: function (name) {
    return this.definitions[name] || null;
  },

  isSupported: function (name) {
    return !!this.getDefinition(name);
  },

  normalize: function (name, value) {
    var definition = this.getDefinition(name) || {};
    var metadata = value || {};

    return {
      plus_error: metadata.plus_error != null ?
        metadata.plus_error : (metadata.plusError != null ? metadata.plusError : null),
      minus_error: metadata.minus_error != null ?
        metadata.minus_error : (metadata.minusError != null ? metadata.minusError : null),
      measurement_method: metadata.measurement_method != null ?
        metadata.measurement_method : (metadata.measurementMethod || null),
      datum: definition.hasDatum ?
        (metadata.datum || definition.defaultDatum || null) : null,
      unit: definition.fixedUnit ||
        metadata.unit || definition.defaultUnit || null
    };
  },

  hasContent: function (value) {
    var hasValue = false;
    Ext.Object.each(value || {}, function (key, item) {
      if (item !== null && item !== undefined && item !== '') {
        hasValue = true;
        return false;
      }
    });
    return hasValue;
  },

  getSummary: function (name, value) {
    var metadata = this.normalize(name, value);
    var parts = [];

    if (metadata.plus_error != null) {
      parts.push('+ error: ' + metadata.plus_error);
    }
    if (metadata.minus_error != null) {
      parts.push('− error: ' + metadata.minus_error);
    }
    if (metadata.measurement_method) {
      parts.push('Method: ' + metadata.measurement_method);
    }
    if (metadata.datum) {
      parts.push('Datum: ' + metadata.datum);
    }
    if (metadata.unit) {
      parts.push('Unit: ' + metadata.unit);
    }

    return parts.join('; ');
  }
});

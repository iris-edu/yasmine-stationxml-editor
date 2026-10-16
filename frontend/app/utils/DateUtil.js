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
* 2019/10/07 : version 2.0.0 initial commit
* 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define("yasmine.utils.DateUtil", {
  singleton: true,
  utcDate: function () {
    let now = new Date();
    return new Date(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(), now.getUTCHours(), now.getUTCMinutes(), now.getUTCSeconds());
  },
  guiFormat: function (style) {
    return style === 'short'
      ? yasmine.Globals.DatePrintShortFormat
      : yasmine.Globals.DatePrintLongFormat;
  },
  formatShort: function (value) {
    if (!value) {
      return '';
    }
    var date = Ext.isDate(value) ? value : Ext.Date.parse(value, yasmine.Globals.DateReadFormat, true);
    return date ? Ext.Date.format(date, yasmine.Globals.DatePrintShortFormat) : '';
  },
  refreshGuiDates: function () {
    Ext.ComponentQuery.query('datefield[yasmineGuiDate]').forEach(function (field) {
      var value = field.getValue();
      field.format = yasmine.utils.DateUtil.guiFormat(field.yasmineGuiDate);
      field.submitFormat = yasmine.Globals.DateReadFormat;
      if (field.picker) {
        field.picker.format = field.format;
      }
      if (value) {
        field.setValue(value);
      }
    });
    Ext.ComponentQuery.query('datecolumn[yasmineGuiDate]').forEach(function (column) {
      column.format = yasmine.utils.DateUtil.guiFormat(column.yasmineGuiDate);
      var filter = column.filter;
      if (filter && filter.isGridFilter) {
        filter.dateFormat = column.format;
        if (filter.menu) {
          filter.menu.destroy();
          filter.menu = null;
        }
      }
    });
    Ext.ComponentQuery.query('grid, treepanel').forEach(function (panel) {
      var view = panel.getView && panel.getView();
      if (view && view.refresh) {
        view.refresh();
      }
    });
    Ext.ComponentQuery.query('dataview').forEach(function (view) {
      if (view.refresh) {
        view.refresh();
      }
    });
    Ext.ComponentQuery.query('treepanel').forEach(function (tree) {
      var root = tree.getRootNode && tree.getRootNode();
      if (!root || !root.cascade) {
        return;
      }
      root.cascade(function (node) {
        if (node.getField && node.getField('text')) {
          node.set('text', node.get('text'));
        }
      });
    });
  }
});

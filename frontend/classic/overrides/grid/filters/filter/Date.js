/* 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov */
Ext.define('overrides.grid.filters.filter.Date', {
  override: 'Ext.grid.filters.filter.Date',

  createMenu: function () {
    var style = this.yasmineGuiDate || (this.column && this.column.yasmineGuiDate);
    if (style) {
      this.dateFormat = style === 'short'
        ? yasmine.Globals.DatePrintShortFormat
        : yasmine.Globals.DatePrintLongFormat;
    }
    this.callParent(arguments);
  },

  getSerializer: function () {
    return function (data) {
      if (data && data.value) {
        data.value = Ext.Date.format(data.value, yasmine.Globals.DateReadFormat);
      }
    };
  }
});

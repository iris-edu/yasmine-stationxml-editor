/* 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov */
Ext.define('overrides.grid.column.Date', {
  override: 'Ext.grid.column.Date',

  initComponent: function () {
    if (this.yasmineGuiDate) {
      this.format = this.yasmineGuiDate === 'short'
        ? yasmine.Globals.DatePrintShortFormat
        : yasmine.Globals.DatePrintLongFormat;
    }
    this.callParent(arguments);
  }
});

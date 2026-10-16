/* 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov */
Ext.define('overrides.form.field.Date', {
  override: 'Ext.form.field.Date',

  initComponent: function () {
    if (this.yasmineGuiDate) {
      this.format = this.yasmineGuiDate === 'short'
        ? yasmine.Globals.DatePrintShortFormat
        : yasmine.Globals.DatePrintLongFormat;
      this.submitFormat = yasmine.Globals.DateReadFormat;
    }
    this.callParent(arguments);
  }
});

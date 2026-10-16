/* 2026-09-27, version 4.4.0-beta: ASGSR, Alexey Emanov */
Ext.define('yasmine.view.userlibrary.UserLibraryImportController', {
  extend: 'Ext.app.ViewController',
  id: 'userLibraryImport-controller',
  alias: 'controller.user-library-import',

  onImportClick: function () {
    var form = this.lookupReference('importForm').getForm();
    var that = this;
    if (this._importRunning || !form.isValid()) {
      return;
    }
    this._importRunning = true;
    form.submit({
      url: '/api/user-library/ie/',
      submitEmptyText: false,
      success: function () {
        that.fireEvent('libraryImported');
        that.closeView();
      },
      failure: function (fp, action) {
        that._importRunning = false;
        var message = (action && action.result && action.result.message)
          || 'Only a FDSN StationXML file can be imported';
        Ext.Msg.alert('Import User Library', message);
      }
    });
  },

  onCancelClick: function () {
    this.closeView();
  }
});

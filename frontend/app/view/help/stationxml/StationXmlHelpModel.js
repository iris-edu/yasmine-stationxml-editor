/* 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov */
Ext.define('yasmine.view.help.stationxml.StationXmlHelpModel', {
  extend: 'Ext.app.ViewModel',
  alias: 'viewmodel.stationxml-help',

  data: {
    loading: true,
    currentPath: null,
    currentTitle: 'StationXML 1.2'
  }
});

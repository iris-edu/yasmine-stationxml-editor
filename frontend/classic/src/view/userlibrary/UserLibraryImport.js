/* 2026-09-24, version 4.3.3-beta: ASGSR, Alexey Emanov */
Ext.define('yasmine.view.userlibrary.UserLibraryImport', {
  extend: 'Ext.window.Window',
  xtype: 'user-library-import',
  requires: [
    'Ext.form.Panel',
    'yasmine.view.userlibrary.UserLibraryImportController'
  ],
  controller: 'user-library-import',
  title: 'Import User Library',
  modal: true,
  frame: false,
  cls: 'yasmine-window',
  constrain: true,
  minWidth: 280,
  listeners: {
    show: function () {
      yasmine.utils.ResponsiveUtil.fitWindow(this, {
        minWidth: 400,
        minHeight: 220,
        width: 480,
        height: 260
      });
    },
    afterlayout: function () {
      yasmine.utils.ResponsiveUtil.clampWindow(this);
    }
  },
  items: {
    xtype: 'form',
    reference: 'importForm',
    width: '100%',
    bodyPadding: 10,
    defaults: {
      anchor: '100%',
      labelWidth: 50
    },
    items: [{
      xtype: 'textfield',
      name: 'name',
      fieldLabel: 'Name',
      allowBlank: true,
      emptyText: 'Leave blank to keep the original name'
    }, {
      xtype: 'filefield',
      emptyText: 'StationXML file',
      fieldLabel: 'XML',
      name: 'xml-path',
      allowBlank: false,
      buttonText: '',
      buttonConfig: {
        iconCls: 'x-fa fa-upload'
      }
    }],
    buttons: [{
      text: 'Upload',
      iconCls: 'x-fa fa-upload',
      cls: 'yasmine-primary-action',
      handler: 'onImportClick'
    }, {
      text: 'Cancel',
      iconCls: 'x-fa fa-ban',
      handler: 'onCancelClick'
    }]
  }
});

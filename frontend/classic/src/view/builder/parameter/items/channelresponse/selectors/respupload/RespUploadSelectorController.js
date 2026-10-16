/* ****************************************************************************
* 2026-10-04, version 4.4.0-beta: ASGSR, Alexey Emanov
*
* Submit Upload RESP form to import-resp and show the response preview.
*
* ****************************************************************************/

Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.selectors.respupload.RespUploadSelectorController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.resp-upload-selector',

  onFileChange: function (field) {
    var btn = this.lookupReference('uploadRespBtn');
    if (btn) {
      btn.setDisabled(!field || !field.getValue());
    }
  },

  onUploadClick: function () {
    var form = this.getView();
    if (!form || !form.isValid()) {
      return;
    }
    var fileField = this.lookupReference('respUploadFile');
    if (!fileField || !fileField.getValue()) {
      Ext.Msg.alert('Upload RESP', 'Please choose a RESP file.');
      return;
    }

    var editor = form.up('yasmine-channel-response-field');
    var editorCtrl = editor && editor.getController();
    var editorVm = editor && editor.getViewModel();
    var record = editorVm && editorVm.get('record');
    var nodeId = yasmine.utils.ResponseRecalculateUtil.nodeInstanceId(record);
    if (nodeId == null || nodeId === '') {
      Ext.Msg.alert('Upload RESP', 'Channel is required.');
      return;
    }

    var sensorField = this.lookupReference('sensorName');
    var dataloggerField = this.lookupReference('dataloggerName');
    var that = this;

    form.submit({
      url: '/api/channel/response/import-resp/',
      params: {
        nodeInstanceId: nodeId,
        createEquipment: '1',
        sensorName: sensorField ? sensorField.getValue() : '',
        dataloggerName: dataloggerField ? dataloggerField.getValue() : ''
      },
      waitMsg: 'Uploading RESP…',
      success: function (fp, action) {
        if (fileField.reset) {
          fileField.reset();
        }
        that.onFileChange(fileField);
        if (editorCtrl && typeof editorCtrl.applyImportedResponse === 'function') {
          editorCtrl.applyImportedResponse(action.result || {});
        }
      },
      failure: function (fp, action) {
        var message = (action && action.result && action.result.message) ||
          'Cannot import RESP file';
        Ext.Msg.alert('Upload RESP', message);
      }
    });
  }
});

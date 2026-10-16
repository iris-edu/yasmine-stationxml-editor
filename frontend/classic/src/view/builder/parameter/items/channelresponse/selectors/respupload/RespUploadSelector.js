/* ****************************************************************************
* 2026-10-04, version 4.4.0-beta: ASGSR, Alexey Emanov
*
* Upload RESP: file plus optional Sensor / Datalogger description names.
*
* ****************************************************************************/

Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.selectors.respupload.RespUploadSelector', {
  extend: 'Ext.form.Panel',
  xtype: 'resp-upload-selector',
  reference: 'resp-upload-selector',
  requires: [
    'Ext.plugin.Responsive',
    'yasmine.view.xml.builder.parameter.items.channelresponse.selectors.respupload.RespUploadSelectorController'
  ],
  controller: 'resp-upload-selector',
  cls: 'yasmine-panel-outline yasmine-response-selector yasmine-resp-upload',
  bodyPadding: 16,
  scrollable: 'y',
  layout: {
    type: 'vbox',
    align: 'stretch'
  },
  plugins: 'responsive',
  responsiveConfig: {
    'width < 768 || height < 500': {
      bodyPadding: 12
    },
    'width >= 768 && height >= 500': {
      bodyPadding: 16
    }
  },
  items: [
    {
      xtype: 'component',
      html: '<b>Upload RESP</b>',
      margin: '0 0 12 0',
      style: {textAlign: 'center'}
    },
    {
      xtype: 'container',
      cls: 'yasmine-resp-upload-fields',
      maxWidth: 520,
      layout: {
        type: 'vbox',
        align: 'stretch'
      },
      defaults: {
        labelAlign: 'top',
        labelWidth: 120,
        margin: '0 0 12 0',
        minWidth: 0,
        width: '100%'
      },
      items: [
        {
          xtype: 'filefield',
          reference: 'respUploadFile',
          name: 'file',
          fieldLabel: 'RESP file',
          allowBlank: false,
          buttonText: 'Browse…',
          buttonConfig: {
            width: undefined
          },
          accept: '.resp,.RESP',
          listeners: {
            change: 'onFileChange'
          }
        },
        {
          xtype: 'textfield',
          reference: 'sensorName',
          name: 'sensorName',
          fieldLabel: 'Sensor Name',
          emptyText: 'Stored as Sensor Description'
        },
        {
          xtype: 'textfield',
          reference: 'dataloggerName',
          name: 'dataloggerName',
          fieldLabel: 'Datalogger Name',
          emptyText: 'Stored as DataLogger Description'
        },
        {
          xtype: 'component',
          html: 'SampleRate is filled from the last decimation stage when present.',
          margin: '0 0 16 0',
          cls: 'yasmine-resp-upload-hint'
        },
        {
          xtype: 'container',
          layout: {
            type: 'hbox',
            pack: 'center'
          },
          items: [{
            xtype: 'button',
            reference: 'uploadRespBtn',
            text: 'Upload',
            iconCls: 'x-fa fa-upload',
            minWidth: 120,
            disabled: true,
            handler: 'onUploadClick'
          }]
        }
      ]
    }
  ]
});

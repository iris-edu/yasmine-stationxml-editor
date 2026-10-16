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
* 2026-09-25, version 4.3.3-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.list.XmlListController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.xml-list',
  requires: [
    'yasmine.view.xml.XmlEdit',
    'yasmine.view.xml.XmlImport',
    'yasmine.model.Xml'
  ],
  listen: {
    controller: {
      '#xmlEdit-controller': {
        xmlSaved: 'onXmlSaved'
      },
      '#xmlImport-controller': {
        xmlImported: 'onXmlImported'
      }
    }
  },
  init: function () {
    this.syncXmlListColumns();
    this.syncXmlToolbar();
    this.mon(Ext.GlobalEvents, 'resize', this.syncXmlListLayout, this, {buffer: 150});
  },
  syncXmlListLayout: function () {
    this.syncXmlListColumns();
    this.syncXmlToolbar();
  },
  syncXmlListColumns: function () {
    var grid = this.getView();
    if (!grid || !yasmine.utils.ResponsiveUtil) {
      return;
    }
    var stack = yasmine.utils.ResponsiveUtil.useStackLayout();
    Ext.Array.each(['module', 'uri', 'sender'], function (dataIndex) {
      var column = grid.down('gridcolumn[dataIndex=' + dataIndex + ']');
      if (column) {
        column.setHidden(stack);
      }
    });
  },
  syncXmlToolbar: function () {
    var grid = this.getView();
    var narrow;
    var createButton;
    var openButton;
    if (!grid || grid.destroyed || !yasmine.utils.ResponsiveUtil) {
      return;
    }
    narrow = yasmine.utils.ResponsiveUtil.useStackLayout();
    createButton = grid.down('#createXmlId');
    openButton = grid.down('#openBuilderId');
    if (createButton) {
      createButton.setText(narrow ? 'New' : 'New XML');
    }
    if (openButton) {
      openButton.setText(narrow ? 'Open' : 'Open Builder');
    }
    if (grid.rendered && yasmine.utils.ResponsiveUtil.syncWrappingToolbars) {
      Ext.defer(function () {
        if (!grid.destroyed) {
          yasmine.utils.ResponsiveUtil.syncWrappingToolbars();
        }
      }, 30);
    }
  },
  onCreateXmlClick: function () {
    let form = Ext.create({xtype: 'xml-edit'});
    let record = new yasmine.model.Xml();
    let now = new Date();
    let settings = yasmine.Globals.Settings || {};
    record.set('source', settings.general__source);
    record.set('module', settings.general__module);
    record.set('uri', settings.general__uri);
    record.set('created_at', new Date(
      now.getUTCFullYear(),
      now.getUTCMonth(),
      now.getUTCDate(),
      now.getUTCHours(),
      now.getUTCMinutes(),
      now.getUTCSeconds()
    ));

    form.getViewModel().set('model', record);
    form.show();
  },
  onEditXmlClick: function () {
    let form = Ext.create({xtype: 'xml-edit'});
    form.getViewModel().set('model', yasmine.model.Xml.load(this.getSelectedRecord().id));
    form.show();
  },
  onDeleteXmlClick: function () {
    Ext.MessageBox.confirm('Confirm', 'Are you sure you want to delete record?', function (btn) {
      if (btn === 'yes') {
        this.deleteSelectedXml();
      }
    }, this);
  },
  onBuildXmlClick: function () {
    this.redirectTo(`xml-builder/${this.getSelectedRecord().id}`);
  },
  deleteSelectedXml: function () {
    this.getView().getStore().remove(this.getSelectedRecord());
  },
  onImportXmlClick: function () {
    Ext.create({xtype: 'xml-import'}).show();
  },
  onExportXmlClick: function () {
    yasmine.store.FileLoader.load(`api/xml/ie/${this.getSelectedRecord().id}`);
  },
  onXmlSaved: function () {
    this.reloadData();
  },
  onXmlImported: function () {
    this.reloadData();
  },
  getSelectedRecord: function () {
    return this.getView().getSelection()[0];
  },
  reloadData: function () {
    this.getView().getStore().reload();
  }
});



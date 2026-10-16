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


Ext.define('yasmine.view.userlibrary.UserLibraryListController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.userlibrary-list',
  requires: [
    'yasmine.view.userlibrary.UserLibraryImport'
  ],
  listen: {
    controller: {
      '#userLibraryImport-controller': {
        libraryImported: 'onLibraryImported'
      }
    }
  },
  init: function () {
    this.syncLibraryToolbar();
    this.mon(Ext.GlobalEvents, 'resize', this.syncLibraryToolbar, this, {buffer: 150});
  },
  syncLibraryToolbar: function () {
    var grid = this.getView();
    var card = yasmine.utils.ResponsiveUtil && yasmine.utils.ResponsiveUtil.useCardLayout();
    var createButton = grid.down('#createLibrary');
    var openButton = grid.down('#openLibrary');
    if (createButton) {
      createButton.setText(card ? 'New' : 'New Library');
    }
    if (openButton) {
      openButton.setText(card ? 'Open' : 'Open Library');
    }
  },
  onCreateLibraryClick: function () {
    let record = new yasmine.model.UserLibrary();
    let grid = this.getView();
    this.getLibraryStore().insert(0, record);
    // The new row is not in the view until the next layout. startEdit
    // before that returns without opening the editor.
    Ext.defer(function () {
      if (grid.destroyed) {
        return;
      }
      if (grid.getView().getNode(record)) {
        this.startEditing(record);
        return;
      }
      Ext.defer(function () {
        if (!grid.destroyed && grid.getView().getNode(record)) {
          this.startEditing(record);
        }
      }, 50, this);
    }, 30, this);
  },
  onEditLibraryClick: function () {
    this.startEditing(this.getSelectedLibrary())
  },
  onDeleteLibraryClick: function () {
    Ext.MessageBox.confirm('Confirm', 'Are you sure you want to delete a selected library?', function (btn) {
      if (btn === 'yes') {
        this.deleteSelectedLibrary();
      }
    }, this);
  },
  onConfigureLibraryClick: function () {
    var grid = this.getView();
    var plugin = grid && grid.findPlugin('rowediting');
    var selected = this.getSelectedLibrary();
    if (plugin && plugin.editing) {
      plugin.cancelEdit();
    }
    if (!selected || selected.phantom || !selected.id) {
      return;
    }
    this.redirectTo('user-library-builder/' + selected.id);
  },
  onImportLibraryClick: function () {
    Ext.create({xtype: 'user-library-import'}).show();
  },
  onExportLibraryClick: function () {
    yasmine.store.FileLoader.load(`api/user-library/ie/${this.getSelectedLibrary().id}`);
  },
  onLibraryImported: function () {
    this.getViewModel().getStore('userLibraryStore').reload();
  },
  startEditing: function (record) {
    this.getView().findPlugin('rowediting').startEdit(record, 0);
  },
  deleteSelectedLibrary: function () {
    this.getLibraryStore().remove(this.getSelectedLibrary());
  },
  getSelectedLibrary: function () {
    return this.getViewModel().get('selectedUserLibrary')
  },
  getLibraryStore: function () {
    return this.getView().getStore('userLibraryStore')
  }
})

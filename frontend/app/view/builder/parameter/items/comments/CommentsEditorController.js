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
* NRLv2 online support (2026): ASGSR, Alexey Emanov.
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
* 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.parameter.items.comments.CommentsEditorController', {
  extend: 'yasmine.view.xml.builder.parameter.ParameterItemEditorController',
  alias: 'controller.comments-editor',
  listen: {
    controller: {
      '#comments-editor-form-controller': {
        commentUpdated: 'onCommentUpdated'
      }
    }
  },
  initData: function () {
    let value = this.getViewModel().get('record').get('value');
    let store = this.getViewModel().getStore('commentStore');
    store.removeAll();

    if (!value) {
      return;
    }

    var items = Array.isArray(value) ? value : [value];
    if (!Array.isArray(items) || items.length === 0) {
      return;
    }
    items.forEach(function (item) {
      if (!item || typeof item !== 'object') return;
      let comment = new yasmine.view.xml.builder.parameter.items.comments.Comment();
      comment.set('id', item.id == null ? null : item.id);
      comment.set('subject', item.subject);
      comment.set('value', item.value);
      comment.set('begin_effective_time', item.begin_effective_time);
      comment.set('end_effective_time', item.end_effective_time);
      comment.set('authors', item.authors || item._authors || []);
      comment.modified = {};
      store.add(comment);
    });
  },
  fillRecord: function () {
    let record = this.getViewModel().get('record');
    let store = this.getViewModel().getStore('commentStore');
    let items = [];
    if (store.getRange) {
      items = store.getRange();
    } else {
      var data = store.getData ? store.getData() : null;
      items = (data && data.items) ? data.items : [];
      if (items.length === 0 && store.each) {
        store.each(function (r) { items.push(r); });
      }
    }
    let comments = items.map(function (item) {
      let data = item.getData ? item.getData() : item;
      return {
        'py/object': 'obspy.core.inventory.util.Comment',
        id: data.id == null ? null : data.id,
        subject: data.subject || null,
        value: data.value || '',
        begin_effective_time: data.begin_effective_time || null,
        end_effective_time: data.end_effective_time || null,
        authors: data.authors || []
      };
    });

    record.set('value', comments);
  },
  validate: function () {
    let errors = [];
    this.getViewModel().getStore('commentStore').each(function (comment, index) {
      if (!Ext.String.trim(comment.get('value') || '')) {
        errors.push('Comment ' + (index + 1) + ' requires a value.');
      }
    });
    this.getViewModel().set('validation.activeErrors', errors);
    if (errors.length) {
      return false;
    }
    return this.callParent(arguments);
  },
  onCommentUpdated: function (record) {
    let store = this.getViewModel().getStore('commentStore');
    if (!store.contains(record)) {
      store.insert(0, record);
    }
    this.fillRecord();
    var grid = this.getView().down('grid');
    if (grid && grid.getView()) {
      grid.getView().refresh();
    }
  },
  onAddClick: function () {
    var comment = new yasmine.view.xml.builder.parameter.items.comments.Comment();
    this.showEditForm(comment);
  },
  onEditClick: function () {
    this.showEditForm(this.getSelectedRecord());
  },
  onDeleteClick: function () {
    var me = this;
    Ext.MessageBox.confirm('Confirm', 'Are you sure you want to delete?', function (btn) {
      if (btn === 'yes') {
        me.getSelectedRecord().drop();
        me.fillRecord();
      }
    }, this);
  },
  getSelectedRecord: function () {
    return this.getViewModel().get('selectedCommentRow');
  },
  showEditForm: function (record) {
    let commentRecord = this.getView().getViewModel().get('record');
    let form = Ext.create({ xtype: 'comments-editor-form' });
    form.getController().initData(record, commentRecord.get('parameterId'), commentRecord.get('node_type_id'));
    form.show();
  }
});

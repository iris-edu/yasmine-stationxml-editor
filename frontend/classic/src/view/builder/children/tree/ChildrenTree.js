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
*
* ****************************************************************************/

// https://forum.sencha.com/forum/showthread.php?328802-6-2-Crash-when-clicking-grid-view-area-outside-cells&p=1159380&viewfull=1#post1159380
Ext.define(null, {
  override: 'Ext.view.Table',

  getDefaultFocusPosition: function (fromComponent) {
    var me = this,
      store = me.dataSource,
      focusPosition = me.lastFocused,
      newPosition = new Ext.grid.CellContext(me).setPosition(0, 0),
      targetCell, scroller;
    if (fromComponent) {
      // Tabbing in from one of our column headers; the user will expect to land in that column.
      // Unless it is configured cellFocusable: false
      if (fromComponent.isColumn && fromComponent.cellFocusable !== false) {
        if (!focusPosition) {
          focusPosition = newPosition;
        }
        focusPosition.setColumn(fromComponent);
        focusPosition.setView(fromComponent.getView());
      }
        // Tabbing in from the neighbouring TableView (eg, locking).
      // Go to column zero, same record
      else if (fromComponent.isTableView && fromComponent.lastFocused) {
        focusPosition = new Ext.grid.CellContext(me).setPosition(fromComponent.lastFocused.record, 0);
      }
    }
    // We found a position from the "fromComponent, or there was a previously focused context
    if (focusPosition) {
      scroller = me.getScrollable();
      // Record is not in the store, or not in the rendered block.
      // Fall back to using the same row index.
      if (!store.contains(focusPosition.record) || (scroller && !scroller.isInView(focusPosition.getRow()).y)) {
        focusPosition.setRow(store.getAt(Math.min(focusPosition.rowIdx, store.getCount() - 1)));
      }
    } else // All else failes, find the first focusable cell.
    {
      focusPosition = newPosition;
      // Find the first focusable cell.
      targetCell = me.el.down(me.getCellSelector() + '[tabIndex="-1"]');
      if (targetCell) {
        focusPosition.setPosition(me.getRecord(targetCell), me.getHeaderByCell(targetCell));
      } else // All visible columns are cellFocusable: false
      {
        focusPosition = null;
      }
    }
    return focusPosition;
  },
});

Ext.define(null, {
  override: 'Ext.grid.CellContext',
  setView: function (view) {
    this.view = view;
    this.refresh();
  },
  setRow: function(row) {
    var me = this,
      dataSource = me.view.dataSource,
      oldRecord = me.record,
      count;
    if (row !== undefined && row !== null) {
      // Row index passed, < 0 meaning count from the tail (-1 is the last, etc)
      if (typeof row === 'number') {
        count = dataSource.getCount();
        row = row < 0 ? Math.max(count + row, 0) : Math.max(Math.min(row, count - 1), 0);
        me.rowIdx = row;
        me.record = dataSource.getAt(row);
      }
      // row is a Record
      else if (row.isModel) {
        me.record = row;
        me.rowIdx = dataSource.indexOf(row);
      }
      // row is a grid row, or Element wrapping row
      else if (row.tagName || row.isElement) {
        me.record = me.view.getRecord(row);
        me.rowIdx = dataSource.indexOf(me.record);
      }
    }
    if (me.record !== oldRecord) {
      me.generation++;
    }
    return me;
  },
});


Ext.define('yasmine.view.xml.builder.children.tree.ChildrenTree', {
  extend: 'Ext.tree.Panel',
  xtype: 'children-tree',
  alias: 'widget.tree-children',
  requires: [
    'yasmine.view.xml.builder.children.tree.ChildrenTreeModel',
    'yasmine.view.xml.builder.children.tree.ChildrenTreeController'
  ],
  rootVisible: true,
  scrollable: true,
  useArrows: true,
  viewModel: 'children-tree',
  controller: 'children-tree',
  viewConfig: {
    loadMask: false
  },
  bind: {
    store: '{treeStore}',
    selection: '{selectedItem}'
  },
  listeners: {
    select: 'onTreeNodeSelect'
  }
});

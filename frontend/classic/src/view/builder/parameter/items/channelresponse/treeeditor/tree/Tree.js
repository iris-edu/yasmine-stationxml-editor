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
* 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.tree.Tree', {
  extend: 'Ext.tree.Panel',
  xtype: 'channel-response-tree',
  requires: [
    'yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.tree.TreeController'
  ],
  controller: 'channel-response-tree',
  rootVisible: true,
  autoScroll: true,
  useArrows: true,
  tbar: [
    {
      iconCls: 'x-fa fa-plus',
      bind: {
        tooltip: '{titleAddNew}',
        disabled: '{!canAddNewNode}'
      },
      menu: {
        listeners: {
          beforeshow: 'onAddMenuBeforeShow'
        },
        items: [
          {
            text: 'Loading schema choices...',
            disabled: true
          }
        ]
      }
    },
    {
      xtype: 'button',
      iconCls: 'x-fa fa-minus',
      handler: 'onDeleteClick',
      disabled: true,
      bind: {
        tooltip: 'Delete <b>{deleteNodeTitle}</b> node',
        disabled: '{!canDelete}'
      }
    },
    {
      xtype: 'tbspacer',
      flex: 1
    },
    {
      xtype: 'button',
      iconCls: 'x-fa fa-expand',
      handler: 'onExpandAll',
      tooltip: 'Expand Tree',
    },
    {
      xtype: 'button',
      iconCls: 'x-fa fa-compress',
      handler: 'onCollapseAll',
      tooltip: 'Collapse Tree',
    }
  ],
  viewConfig: {
    loadMask: false
  },
  listeners: {
    select: 'onResponseNodeSelect',
    afterrender: function() {
      let store = this.getStore();
      if (!store || store.isEmptyStore) {
        return;
      }
      let root = store.getRootNode && store.getRootNode();
      if (root && root.get && root.get('key')) {
        this.getSelectionModel().select(root);
      }
    }
  }
});

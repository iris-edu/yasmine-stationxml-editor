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
* 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.userlibrary.builder.UserLibraryBuilderController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.userlibrary-builder',
  init: function () {
    this.mon(this.getView(), 'afterrender', this.syncLibraryLayout, this);
    this.mon(Ext.GlobalEvents, 'resize', this.syncLibraryLayout, this, {buffer: 200});
  },
  initModel: function (libraryId) {
    let record = new yasmine.model.UserLibrary({ id: libraryId });
    let viewModel = this.getViewModel();
    record.load({
      scope: this,
      success: function (record) {
        if (!viewModel || this.getView().destroyed) {
          return;
        }
        viewModel.set('selectedLibrary', record);
        viewModel.set('storeLibraryId', record.get('id'));
        viewModel.set('storeNodeType', yasmine.NodeTypeEnum.network);
        viewModel.notify();
      }
    });
  },
  onNodeTypeSelected: function (container, button) {
    let nodeTypeMap = {
      'type_1': yasmine.NodeTypeEnum.network,
      'type_2': yasmine.NodeTypeEnum.station,
      'type_3': yasmine.NodeTypeEnum.channel
    };
    Ext.ux.Mediator.fireEvent('children-reload', nodeTypeMap[button.itemId]);
  },
  syncLibraryLayout: function () {
    var workspace = this.lookup('libraryWorkspace');
    var switcher = this.lookup('libraryPaneSwitcher');
    var children;
    var params;
    var useCard;
    var wasCard;
    if (!workspace || !yasmine.utils.ResponsiveUtil) {
      return;
    }
    children = this.lookup('libraryChildren');
    params = this.lookup('parameter-editor');
    useCard = yasmine.utils.ResponsiveUtil.useCardLayout();
    wasCard = this._libraryCardLayout;
    this._libraryCardLayout = useCard;
    var paneBar = this.getView().down('#libraryPaneBar');
    if (useCard) {
      if (paneBar) {
        paneBar.show();
      }
      if (switcher) {
        switcher.show();
      }
      // Only reset to Hierarchy when entering card layout, not on every resize.
      if (!wasCard) {
        if (switcher) {
          switcher.items.each(function (btn, index) {
            btn.setPressed(index === 0);
          });
        }
        if (children) {
          children.show();
        }
        if (params) {
          params.hide();
        }
      }
    } else {
      if (paneBar) {
        paneBar.hide();
      }
      if (switcher) {
        switcher.hide();
      }
      if (children) {
        children.show();
      }
      if (params) {
        params.show();
      }
    }
    if (workspace && workspace.updateLayout) {
      workspace.updateLayout();
    }
    this.syncLibraryTypeLabels();
    Ext.defer(function () {
      yasmine.utils.ResponsiveUtil.syncWrappingToolbars();
    }, 30);
  },
  syncLibraryTypeLabels: function () {
    var switcher = this.lookup('libraryTypeSwitcher');
    var shortLabels;
    if (!switcher || switcher.destroyed) {
      return;
    }
    shortLabels = yasmine.utils.ResponsiveUtil.useTopHeader();
    switcher.items.each(function (btn) {
      var full;
      var next;
      if (!btn || btn.destroyed || !btn.setText) {
        return;
      }
      if (btn._fullText == null) {
        btn._fullText = btn.getText() || '';
      }
      full = btn._fullText;
      next = shortLabels ? full.replace(/ Library$/, '') : full;
      if (btn.getText() !== next) {
        btn.setText(next);
      }
      if (btn.setTooltip) {
        btn.setTooltip(shortLabels && next !== full ? full : '');
      }
    });
  },
  onLibraryPaneToggle: function (container, button, pressed) {
    if (!pressed || !yasmine.utils.ResponsiveUtil.useCardLayout()) {
      return;
    }
    var workspace = this.lookup('libraryWorkspace');
    var children;
    var params;
    if (!workspace) {
      return;
    }
    children = this.lookup('libraryChildren');
    params = this.lookup('parameter-editor');
    if (button.getItemId() === 'detail') {
      if (children) {
        children.hide();
      }
      if (params) {
        params.show();
      }
    } else {
      if (children) {
        children.show();
      }
      if (params) {
        params.hide();
      }
    }
    if (workspace.updateLayout) {
      workspace.updateLayout();
    }
  }
});

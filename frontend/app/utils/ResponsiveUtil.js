/* ****************************************************************************
 * 2026-09-22, version 4.2.0-beta: ASGSR, Alexey Emanov
 *
 * Viewport-class helpers for Classic UI.
 *
 * Layout follows CSS viewport width/height, not device names.
 * Minimum supported viewport: 320 CSS px. Wearables are out of scope.
 *
 * NRLv2 online support (2026): ASGSR, Alexey Emanov.
 *
 * ****************************************************************************/

Ext.define('yasmine.utils.ResponsiveUtil', {
  singleton: true,

  MIN_WIDTH: 320,
  STACK_MAX: 767,
  COMPACT_HEIGHT: 500,
  HEADER_LEFT_MIN: 1280,
  COMPARISON_SPLIT_MIN: 1280,
  COMPARISON_CHART_MIN: 240,
  WIDE_MIN: 1920,
  ULTRAWIDE_MIN: 2560,
  EAST_MAX_WIDTH: 720,
  HELP_MAX_WIDTH: 480,
  STATIONXML_HELP_MAX_WIDTH: 1200,

  BODY_CLASSES: [
    'yasmine-vp-xs',
    'yasmine-vp-sm',
    'yasmine-vp-md',
    'yasmine-vp-lg',
    'yasmine-vp-xl',
    'yasmine-vp-xxl',
    'yasmine-vp-uw',
    'yasmine-compact-height'
  ],

  getSize: function () {
    var width = Ext.Element.getViewportWidth();
    var height = Ext.Element.getViewportHeight();
    return {
      width: Math.max(width || 0, 1),
      height: Math.max(height || 0, 1)
    };
  },

  getWidth: function () {
    return this.getSize().width;
  },

  getHeight: function () {
    return this.getSize().height;
  },

  isCompactHeight: function () {
    return this.getHeight() < this.COMPACT_HEIGHT;
  },

  getViewportClass: function () {
    var width = this.getWidth();
    if (width < 360) {
      return 'xs';
    }
    if (width < 768) {
      return 'sm';
    }
    if (width < 1024) {
      return 'md';
    }
    if (width < 1280) {
      return 'lg';
    }
    if (width < 1920) {
      return 'xl';
    }
    if (width < 2560) {
      return 'xxl';
    }
    return 'uw';
  },

  useStackLayout: function () {
    return this.getWidth() <= this.STACK_MAX || this.isCompactHeight();
  },

  useIconOnlyTabs: function () {
    return this.getWidth() <= this.STACK_MAX || this.isCompactHeight();
  },

  useCardLayout: function () {
    return this.useStackLayout();
  },

  useTopHeader: function () {
    return this.getWidth() < this.HEADER_LEFT_MIN || this.isCompactHeight();
  },

  useComparisonSplit: function () {
    return this.getWidth() >= this.COMPARISON_SPLIT_MIN && !this.isCompactHeight();
  },

  // Classic forbids replacing layout type after render (hbox ↔ vbox). Box
  // layouts share DOM wrappers, so flip orientation with setVertical instead.
  applyBoxOrientation: function (container, vertical, options) {
    var layout;
    var changed = false;
    var nextAlign;
    var nextFlex;
    var nextMinHeight;
    options = options || {};
    if (!container || container.destroyed) {
      return false;
    }
    layout = container.getLayout && container.getLayout();
    nextAlign = options.align;
    nextFlex = options.flex;
    nextMinHeight = options.minHeight;
    if (layout && typeof layout.setVertical === 'function') {
      if (!!layout.vertical !== !!vertical) {
        layout.setVertical(!!vertical);
        changed = true;
      }
      if (nextAlign && layout.setAlign) {
        if (!layout.getAlign || layout.getAlign() !== nextAlign) {
          layout.setAlign(nextAlign);
          changed = true;
        }
      }
    } else if (!container.rendered && container.setLayout) {
      container.setLayout({
        type: vertical ? 'vbox' : 'hbox',
        align: nextAlign || 'stretch'
      });
      changed = true;
    }
    if (nextFlex != null && container.flex !== nextFlex) {
      if (container.setFlex) {
        container.setFlex(nextFlex);
      } else {
        container.flex = nextFlex;
      }
      changed = true;
    }
    if (nextMinHeight != null && container.minHeight !== nextMinHeight) {
      if (container.setMinHeight) {
        container.setMinHeight(nextMinHeight);
      } else {
        container.minHeight = nextMinHeight;
      }
      changed = true;
    }
    if (changed && container.updateLayout) {
      container.updateLayout();
    }
    return changed;
  },

  applyComparisonSplit: function (container) {
    if (!container || container.destroyed) {
      return;
    }
    if (this.useComparisonSplit()) {
      this.applyBoxOrientation(container, false, {
        align: 'stretch',
        flex: 1,
        minHeight: 220
      });
    } else {
      this.applyBoxOrientation(container, true, {
        align: 'stretch',
        flex: 1,
        minHeight: this.COMPARISON_CHART_MIN * 2
      });
    }
  },

  isWide: function () {
    return this.getWidth() >= this.WIDE_MIN;
  },

  isUltrawide: function () {
    return this.getWidth() >= this.ULTRAWIDE_MIN;
  },

  getSplitPercent: function (isBuilder) {
    if (isBuilder) {
      return '40%';
    }
    return this.getWidth() >= this.HEADER_LEFT_MIN ? '70%' : '50%';
  },

  getEastMaxWidth: function (isBuilder) {
    if (isBuilder && this.isUltrawide()) {
      return this.EAST_MAX_WIDTH + 160;
    }
    if (isBuilder && this.isWide()) {
      return this.EAST_MAX_WIDTH;
    }
    return undefined;
  },

  fillViewport: function (win, viewWidth, viewHeight) {
    if (!win || win.destroyed || !win.rendered || !win.el) {
      return;
    }
    viewWidth = viewWidth || this.getWidth();
    viewHeight = viewHeight || this.getHeight();
    if (win.setMinWidth) {
      win.setMinWidth(Math.min(280, viewWidth));
    }
    if (win.setMinHeight) {
      win.setMinHeight(Math.min(200, viewHeight));
    }
    if (win.setMaxWidth) {
      win.setMaxWidth(viewWidth);
    }
    if (win.setMaxHeight) {
      win.setMaxHeight(viewHeight);
    }
    if (win.maximize && !win.maximized) {
      win.maximize();
    }
    // iOS maximize often leaves a side gap; pin to the visual viewport.
    if (win.setSize) {
      win.setSize(viewWidth, viewHeight);
    }
    if (win.setPagePosition) {
      win.setPagePosition(0, 0);
    } else {
      if (win.setX) {
        win.setX(0);
      }
      if (win.setY) {
        win.setY(0);
      }
    }
  },

  fitMinWidth: function (preferred) {
    var available = Math.max(0, this.getWidth() - 16);
    return Math.min(preferred || 0, available);
  },

  fitWindow: function (win, options) {
    options = options || {};
    if (!win || win.destroyed || !win.rendered || !win.el) {
      return;
    }
    var viewSize = this.getSize();
    var viewWidth = viewSize.width;
    var viewHeight = viewSize.height;

    if (win.setMaxWidth) {
      win.setMaxWidth(viewWidth);
    }
    if (win.setMaxHeight) {
      win.setMaxHeight(viewHeight);
    }

    if (this.useStackLayout()) {
      this.fillViewport(win, viewWidth, viewHeight);
      return;
    }

    if (win.maximized) {
      return;
    }

    var preferredWidth = options.width || Math.min(1000, Math.floor(viewWidth * 0.85));
    var preferredHeight = options.height || Math.min(700, Math.floor(viewHeight * 0.85));
    var minWidth = Math.min(options.minWidth || 800, viewWidth);
    var minHeight = Math.min(options.minHeight || 500, viewHeight);

    win.setMinWidth(minWidth);
    win.setMinHeight(minHeight);
    win.setSize(
      Math.max(minWidth, Math.min(preferredWidth, viewWidth)),
      Math.max(minHeight, Math.min(preferredHeight, viewHeight))
    );
    if (win.center) {
      win.center();
    }
    this.clampWindow(win);
  },

  clampWindow: function (win) {
    if (!win || win.destroyed || !win.rendered || !win.el) {
      return;
    }
    var viewSize = this.getSize();
    var viewWidth = viewSize.width;
    var viewHeight = viewSize.height;
    var width;
    var height;
    var x;
    var y;

    if (win.setMaxWidth) {
      win.setMaxWidth(viewWidth);
    }
    if (win.setMaxHeight) {
      win.setMaxHeight(viewHeight);
    }
    if (win.minWidth > viewWidth && win.setMinWidth) {
      win.setMinWidth(Math.min(280, viewWidth));
    }
    if (win.minHeight > viewHeight && win.setMinHeight) {
      win.setMinHeight(Math.min(200, viewHeight));
    }
    if (this.useStackLayout()) {
      this.fillViewport(win, viewWidth, viewHeight);
      return;
    }
    if (win.maximized) {
      return;
    }

    width = win.getWidth();
    height = win.getHeight();
    if (width > viewWidth) {
      win.setWidth(viewWidth);
    }
    if (height > viewHeight) {
      win.setHeight(viewHeight);
    }
    x = win.getX();
    y = win.getY();
    width = win.getWidth();
    height = win.getHeight();
    if (x < 0) {
      win.setX(0);
      x = 0;
    }
    if (y < 0) {
      win.setY(0);
      y = 0;
    }
    if (x + width > viewWidth) {
      win.setX(Math.max(0, viewWidth - width));
    }
    if (y + height > viewHeight) {
      win.setY(Math.max(0, viewHeight - height));
    }
  },

  fitHelpWindow: function (win) {
    if (!win || win.destroyed || !win.rendered || !win.el) {
      return;
    }
    var viewSize = this.getSize();
    if (this.useStackLayout()) {
      win.setMaxWidth(undefined);
      win.setWidth(Math.floor(viewSize.width * 0.92));
      win.setHeight(Math.floor(viewSize.height * 0.8));
      win.center();
      return;
    }
    win.setMaxWidth(this.HELP_MAX_WIDTH);
    win.setWidth(Math.min(this.HELP_MAX_WIDTH, Math.floor(viewSize.width * 0.3)));
    win.setHeight(Math.floor(viewSize.height * 0.8));
  },

  fitStationXmlHelpWindow: function (win) {
    if (!win || win.destroyed || !win.rendered || !win.el) {
      return;
    }
    var viewSize = this.getSize();
    if (this.useStackLayout()) {
      this.fillViewport(win, viewSize.width, viewSize.height);
      return;
    }
    win.restore();
    win.setMaxWidth(viewSize.width);
    win.setMaxHeight(viewSize.height);
    win.setSize(
      Math.min(this.STATIONXML_HELP_MAX_WIDTH, Math.floor(viewSize.width * 0.9)),
      Math.min(800, Math.floor(viewSize.height * 0.86))
    );
    win.center();
    this.clampWindow(win);
  },

  applyBodyCls: function () {
    var body = Ext.getBody();
    if (!body) {
      return;
    }
    Ext.Array.each(this.BODY_CLASSES, function (cls) {
      body.removeCls(cls);
    });
    body.addCls('yasmine-vp-' + this.getViewportClass());
    if (this.isCompactHeight()) {
      body.addCls('yasmine-compact-height');
    }
    this.syncHeaderBrand();
    this.syncNavTabs();
    this.syncHeaderTools();
    this.syncWrappingToolbars();
    this.clampVisibleWindows();
  },

  // Header tools are 16px in the Triton theme. Compact CSS gives them a
  // 44×44 touch target, so keep the component box aligned with the icon.
  syncHeaderTools: function () {
    var enlarge;
    var headers;
    if (!Ext.ComponentQuery) {
      return;
    }
    enlarge = this.useStackLayout();
    headers = Ext.ComponentQuery.query('header');
    Ext.Array.each(headers, function (header) {
      var changed = false;
      if (!header || header.destroyed || !header.rendered) {
        return;
      }
      if (header.ui === 'navigation' || (header.hasCls && header.hasCls('x-panel-header-navigation'))) {
        return;
      }
      if (!header.items || !header.items.each) {
        return;
      }
      header.items.each(function (tool) {
        if (!tool || tool.destroyed || !tool.isTool) {
          return;
        }
        if (enlarge) {
          if (tool.width !== 44 || tool.height !== 44) {
            tool._yasmineToolSized = true;
            tool.setSize(44, 44);
            changed = true;
          }
        } else if (tool._yasmineToolSized) {
          tool._yasmineToolSized = false;
          tool.setSize(null, null);
          changed = true;
        }
      });
      if (changed && header.updateLayout) {
        header.updateLayout();
      }
    });
  },

  bind: function () {
    var me = this;
    me.applyBodyCls();
    if (!me._toolbarHooked && Ext.toolbar && Ext.toolbar.Toolbar) {
      me._toolbarHooked = true;
      Ext.toolbar.Toolbar.override({
        afterRender: function () {
          this.callParent(arguments);
          Ext.defer(function () {
            me.syncWrappingToolbars();
          }, 20);
        }
      });
    }
    if (!me._headerToolHooked && Ext.panel && Ext.panel.Header) {
      me._headerToolHooked = true;
      Ext.panel.Header.override({
        afterRender: function () {
          this.callParent(arguments);
          Ext.defer(function () {
            me.syncHeaderTools();
          }, 1);
        }
      });
    }
    Ext.on('resize', function () {
      me.applyBodyCls();
      me.syncViewportSize();
    });
    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', function () {
        me.applyBodyCls();
        me.syncViewportSize();
      });
    }
    // iOS Safari often reports 0x0 on the first layout pass.
    Ext.defer(function () {
      me.applyBodyCls();
      me.syncViewportSize();
    }, 50);
  },

  syncViewportSize: function () {
    if (!Ext.ComponentQuery) {
      return;
    }
    var main = Ext.ComponentQuery.query('app-main')[0];
    if (main && !main.destroyed && main.handleViewportResize) {
      main.handleViewportResize();
    }
    this.syncWrappingToolbars();
    this.clampVisibleWindows();
  },

  // iPad widths (768–1023) keep the two-column layout, but toolbars still
  // have to wrap. Otherwise Map, Epoch, and Import sit past the edge.
  useToolbarWrap: function () {
    return this.getWidth() < 1024 || this.isCompactHeight();
  },

  isWrappingToolbar: function (toolbar) {
    if (!toolbar || toolbar.destroyed) {
      return false;
    }
    if (toolbar.isXType && (toolbar.isXType('tabbar') || toolbar.isXType('breadcrumb'))) {
      return false;
    }
    return this.useToolbarWrap();
  },

  syncWrappingToolbars: function () {
    var me = this;
    if (!Ext.ComponentQuery) {
      return;
    }
    Ext.Array.each(Ext.ComponentQuery.query('toolbar'), function (toolbar) {
      var inner;
      var height;
      var nextHeight;
      if (!toolbar || toolbar.destroyed || !toolbar.rendered || !toolbar.el) {
        return;
      }
      if (toolbar.isXType && (toolbar.isXType('tabbar') || toolbar.isXType('breadcrumb'))) {
        return;
      }
      if (me.isWrappingToolbar(toolbar)) {
        inner = toolbar.el.down('.x-box-inner');
        height = inner && inner.dom ? inner.dom.scrollHeight : 0;
        toolbar.items.each(function (item) {
          var box;
          var toolbarBox;
          if (!item || item.destroyed || !item.getBox || (item.isVisible && !item.isVisible())) {
            return;
          }
          box = item.getBox();
          toolbarBox = toolbar.getBox();
          if (box && toolbarBox) {
            height = Math.max(height, box.y + box.height - toolbarBox.y);
          }
        });
        if (height > 0 && toolbar.setHeight) {
          nextHeight = Math.max(height + 8, 44);
          // Docked Hierarchy/Parameters bars need any positive delta —
          // a 1–2px miss after Epoch wraps still covers Inventory.
          var heightDelta = Math.abs((toolbar.getHeight() || 0) - nextHeight);
          var forceDockSync = toolbar.dock && toolbar.hasCls &&
            (toolbar.hasCls('children-control-bar') || toolbar.hasCls('parameter-list-bar'));
          if (heightDelta > 2 || (forceDockSync && heightDelta > 0)) {
            toolbar._yasmineWrapped = true;
            toolbar.setHeight(nextHeight);
            if (toolbar.dock && toolbar.ownerCt && toolbar.ownerCt.updateLayout) {
              toolbar.ownerCt.updateLayout();
            }
          }
        }
      } else if (toolbar._yasmineWrapped) {
        toolbar._yasmineWrapped = false;
        if (toolbar.setHeight) {
          toolbar.setHeight(null);
        }
        if (toolbar.updateLayout) {
          toolbar.updateLayout();
        }
      }
    });
  },

  clampVisibleWindows: function () {
    var me = this;
    if (!Ext.ComponentQuery) {
      return;
    }
    Ext.Array.each(Ext.ComponentQuery.query('window{isVisible()}'), function (win) {
      if (!win || win.destroyed) {
        return;
      }
      me.clampWindow(win);
    });
  },

  syncHeaderBrand: function () {
    var main, header, titleCmp;
    if (!Ext.ComponentQuery) {
      return;
    }
    main = Ext.ComponentQuery.query('app-main')[0];
    if (!main || main.destroyed || !main.getHeader) {
      return;
    }
    header = main.getHeader();
    if (!header || header.destroyed) {
      return;
    }
    titleCmp = header.getTitle && header.getTitle();
    if (titleCmp && !titleCmp.destroyed && titleCmp.setWidth) {
      // ExtJS ignores setWidth(undefined); null clears the 44px
      // icon-only width so YASMINE can shrink-wrap again.
      titleCmp.setWidth(this.useTopHeader() ? 44 : null);
    }
    if (header.updateLayout) {
      header.updateLayout();
    }
  },

  syncNavTabs: function () {
    var main, tabBar, iconOnly;
    if (!Ext.ComponentQuery) {
      return;
    }
    main = Ext.ComponentQuery.query('app-main')[0];
    if (!main || main.destroyed || !main.getTabBar) {
      return;
    }
    tabBar = main.getTabBar();
    if (!tabBar || tabBar.destroyed) {
      return;
    }
    iconOnly = this.useIconOnlyTabs();
    tabBar.items.each(function (tab) {
      var fullText;
      if (!tab || tab.destroyed || !tab.setText) {
        return;
      }
      if (tab._fullText == null) {
        tab._fullText = tab.getText() || '';
      }
      fullText = tab._fullText;
      if (iconOnly) {
        if (tab.getText()) {
          tab.setText('');
        }
        if (tab.setTooltip && fullText) {
          tab.setTooltip(fullText);
        }
      } else {
        if (tab.getText() !== fullText) {
          tab.setText(fullText);
        }
        if (tab.setTooltip) {
          tab.setTooltip('');
        }
      }
    });
    if (tabBar.updateLayout) {
      tabBar.updateLayout();
    }
  }
});

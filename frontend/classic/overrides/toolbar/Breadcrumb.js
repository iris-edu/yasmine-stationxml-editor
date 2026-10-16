/* ****************************************************************************
 * 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
 * Override: Breadcrumb - always update arrow when node has children
 * Fixes missing arrow (>) after manufacturer when children are loaded async
 *
 * NRLv2 online support (2026): ASGSR, Alexey Emanov.
 * ****************************************************************************/
Ext.define('overrides.toolbar.Breadcrumb', {
  override: 'Ext.toolbar.Breadcrumb',

  updateSelection: function (node, prevNode) {
    var me = this,
      buttons = me._buttons,
      items = [],
      itemCount = Ext.ComponentQuery.query('[isCrumb]', me.getRefItems()).length,
      needsSync = me._needsSync,
      displayField = me.getDisplayField(),
      showIcons, glyph, iconCls, icon, newItemCount, currentNode, text, button, id, depth, i;

    Ext.suspendLayouts();

    if (node) {
      currentNode = node;
      depth = node.get('depth');
      newItemCount = depth + 1;
      i = depth;

      while (currentNode) {
        id = currentNode.getId();
        button = buttons[i];

        // Don't break when node has children - we must update arrow visibility
        if (!needsSync && button && button._breadcrumbNodeId === id && !currentNode.hasChildNodes()) {
          break;
        }

        text = currentNode.get(displayField);

        if (button) {
          button.setText(text);
        } else {
          button = buttons[i] = Ext.create({
            isCrumb: true,
            xtype: me.getUseSplitButtons() ? 'splitbutton' : 'button',
            ui: me.getButtonUI(),
            cls: me._btnCls + ' ' + me._btnCls + '-' + me.ui,
            text: text,
            showEmptyMenu: true,
            menu: {
              listeners: {
                click: '_onMenuClick',
                beforeshow: '_onMenuBeforeShow',
                scope: me
              }
            },
            handler: '_onButtonClick',
            scope: me
          });
        }

        showIcons = me.getShowIcons();

        if (showIcons !== false) {
          glyph = currentNode.get('glyph');
          icon = currentNode.get('icon');
          iconCls = currentNode.get('iconCls');

          if (glyph) {
            button.setGlyph(glyph);
            button.setIcon(null);
            button.setIconCls(iconCls);
          } else if (icon) {
            button.setGlyph(null);
            button.setIconCls(null);
            button.setIcon(icon);
          } else if (iconCls) {
            button.setGlyph(null);
            button.setIcon(null);
            button.setIconCls(iconCls);
          } else if (showIcons) {
            button.setGlyph(null);
            button.setIcon(null);
            button.setIconCls(
              (currentNode.isLeaf() ? me._leafIconCls : me._folderIconCls) + '-' + me.ui
            );
          } else {
            button.setGlyph(null);
            button.setIcon(null);
            button.setIconCls(null);
          }
        }

        button.setArrowVisible(currentNode.hasChildNodes());
        button._breadcrumbNodeId = currentNode.getId();

        currentNode = currentNode.parentNode;
        i--;
      }

      if (newItemCount > itemCount) {
        items = buttons.slice(itemCount, depth + 1);
        me.add(items);
      } else {
        for (i = itemCount - 1; i >= newItemCount; i--) {
          me.remove(buttons[i], false);
        }
      }

    } else {
      for (i = 0; i < buttons.length; i++) {
        me.remove(buttons[i], false);
      }
    }

    Ext.resumeLayouts(true);
    me._syncHelpButtons(node);

    me.fireEvent('selectionchange', me, node, prevNode);

    if (me._shouldFireChangeEvent) {
      me.fireEvent('change', me, node, prevNode);
    }
    me._shouldFireChangeEvent = true;

    me._needsSync = false;
  },

  _syncHelpButtons: function (node) {
    var me = this;
    var helpButtons = me._helpButtons || (me._helpButtons = []);
    var needed = {};
    var current = node;
    var depth, btn, crumb, idx;

    while (current) {
      var help = current.get ? current.get('help') : '';
      help = help ? String(help).trim() : '';
      if (help && current.get('depth') != null) {
        needed[current.get('depth')] = {
          help: help,
          label: me._helpButtonLabel(current)
        };
      }
      current = current.parentNode;
    }

    for (depth = helpButtons.length - 1; depth >= 0; depth--) {
      btn = helpButtons[depth];
      if (btn && !Object.prototype.hasOwnProperty.call(needed, depth)) {
        btn.destroy();
        helpButtons[depth] = null;
      }
    }

    if (!me._helpLayoutHook) {
      me._helpLayoutHook = true;
      me.on('afterlayout', function () {
        me._placeHelpButtons();
      });
    }

    for (depth in needed) {
      if (!Object.prototype.hasOwnProperty.call(needed, depth)) {
        continue;
      }
      depth = parseInt(depth, 10);
      crumb = me._buttons[depth];
      if (!crumb) {
        continue;
      }
      btn = helpButtons[depth];
      if (!btn) {
        btn = helpButtons[depth] = Ext.create({
          xtype: 'button',
          text: 'Model help',
          ui: 'default-toolbar',
          cls: 'yasmine-breadcrumb-help',
          _helpText: '',
          margin: 0,
          padding: '0 8',
          style: 'position:absolute;z-index:5;',
          listeners: {
            click: function (button, event) {
              if (event && event.stopEvent) {
                event.stopEvent();
              }
              Ext.create('Ext.window.Window', {
                title: button.getText() || 'Model help',
                modal: true,
                width: 560,
                height: 380,
                layout: 'fit',
                bodyPadding: 8,
                items: [{
                  xtype: 'textarea',
                  readOnly: true,
                  value: button._helpText || '',
                  fieldStyle: 'font-family: inherit; white-space: pre-wrap;'
                }],
                buttons: [{
                  text: 'Close',
                  handler: function (closeButton) {
                    closeButton.up('window').close();
                  }
                }]
              }).show();
            }
          }
        });
      }
      btn._helpText = needed[depth].help;
      btn.setText(needed[depth].label);
      btn._helpCrumb = crumb;
      if (!btn.rendered) {
        if (me.el) {
          me.el.setStyle('position', 'relative');
          btn.render(me.el);
        }
      }
    }
    me._placeHelpButtons();
  },

  _helpButtonLabel: function (node) {
    var text = node && node.get ? String(node.get('text') || '').replace(/<[^>]+>/g, '') : '';
    var normalized = text.toLowerCase();
    if (normalized.indexOf('select the model') >= 0) {
      return 'Configuration help';
    }
    if (normalized.indexOf('select the manufacturer') >= 0) {
      return 'Model help';
    }
    return 'Help';
  },

  _helpButtonTop: function (crumb, btn, parentTop) {
    var wrap = crumb.getEl().down('.x-btn-wrap');
    var anchorTop = crumb.getEl().getY();
    var anchorHeight = crumb.getHeight();
    var afterStyle, parsedTop, parsedHeight;
    if (wrap) {
      afterStyle = window.getComputedStyle(wrap.dom, ':after');
      parsedTop = parseFloat(afterStyle.top);
      parsedHeight = parseFloat(afterStyle.height);
      if (!isNaN(parsedHeight) && parsedHeight > 0) {
        anchorTop = wrap.getY() + (isNaN(parsedTop) ? 0 : parsedTop);
        anchorHeight = parsedHeight;
      }
    }
    return Math.round(anchorTop - parentTop + (anchorHeight - btn.getHeight()) / 2);
  },

  _placeHelpButtons: function () {
    var me = this;
    var helpButtons = me._helpButtons || [];
    var depth, btn, crumb, crumbXY, parentXY, top;
    if (!me.el) {
      return;
    }
    for (depth = 0; depth < helpButtons.length; depth++) {
      btn = helpButtons[depth];
      crumb = btn && btn._helpCrumb;
      if (!btn || !btn.rendered || !crumb || !crumb.rendered || crumb.destroyed) {
        continue;
      }
      crumbXY = crumb.getEl().getXY();
      parentXY = me.el.getXY();
      top = me._helpButtonTop(crumb, btn, parentXY[1]);
      btn.el.setStyle({
        left: (crumbXY[0] - parentXY[0] + crumb.getWidth() + 12) + 'px',
        top: top + 'px'
      });
    }
  },

  privates: {
    _onMenuBeforeShow: function (menu) {
      var shown = this.callParent(arguments);
      var store;
      if (shown === false) {
        return false;
      }
      this._ensureMenuDragScroll(menu);
      store = this.getStore();
      if (!store || !menu.items) {
        return;
      }
      menu.items.each(function (item) {
        var nodeId = item._breadcrumbNodeId;
        var node = nodeId != null ? store.getNodeById(nodeId) : null;
        if (!node) {
          return;
        }
        var id = String(node.getId() || '');
        var isPlaceholder = node.get('_emptyPlaceholder') ||
          (id.length >= 7 && id.substring(id.length - 7) === '/_empty');
        if (isPlaceholder) {
          item.setDisabled(true);
        }
      });
    },

    // Phone: the menu's up/down chevrons are too small to tap. Drag anywhere
    // on the open list to scroll it. A short tap still selects the item.
    // beforeshow runs before the floating menu is rendered, so bind on show.
    _ensureMenuDragScroll: function (menu) {
      if (!menu || menu._dragScrollBound) {
        return;
      }
      if (menu.el) {
        this._enableMenuDragScroll(menu);
        return;
      }
      if (menu._dragScrollShowHook) {
        return;
      }
      menu._dragScrollShowHook = true;
      menu.on('show', function () {
        this._enableMenuDragScroll(menu);
      }, this);
    },

    _enableMenuDragScroll: function (menu) {
      var startY, lastY, dragging, threshold;

      if (!menu || menu._dragScrollBound || !menu.el) {
        return;
      }
      menu._dragScrollBound = true;
      threshold = 8;
      menu.el.setStyle({
        'touch-action': 'none',
        '-ms-touch-action': 'none'
      });

      menu.el.on({
        pointerdown: function (e) {
          var dom = menu.el.dom;
          var pointerId = e.browserEvent && e.browserEvent.pointerId;
          menu._suppressNextClick = false;
          startY = e.getY();
          lastY = startY;
          dragging = false;
          if (dom.setPointerCapture && pointerId != null) {
            try {
              dom.setPointerCapture(pointerId);
            } catch (ignore) {
              // Capture can fail if the pointer is already gone.
            }
          }
        },
        pointermove: function (e) {
          var y, layout, overflow, innerCt, maxScroll;
          if (startY == null) {
            return;
          }
          y = e.getY();
          layout = menu.getLayout();
          overflow = layout && layout.overflowHandler;
          innerCt = layout && layout.innerCt;
          if (!overflow || !overflow.scrollBy || !overflow.getMaxScrollPosition ||
              !innerCt || !innerCt.lastBox) {
            return;
          }
          maxScroll = overflow.getMaxScrollPosition();
          if (!maxScroll) {
            return;
          }
          if (!dragging) {
            if (Math.abs(y - startY) < threshold) {
              return;
            }
            dragging = true;
            menu._suppressNextClick = true;
          }
          overflow.scrollBy(lastY - y, false);
          lastY = y;
          e.preventDefault();
        },
        pointerup: function (e) {
          var wasDragging = dragging;
          startY = null;
          lastY = null;
          dragging = false;
          if (!wasDragging) {
            return;
          }
          menu._suppressNextClick = true;
          e.preventDefault();
        },
        pointercancel: function () {
          startY = null;
          lastY = null;
          dragging = false;
        }
      });

      menu.el.on('click', function (e) {
        if (!menu._suppressNextClick) {
          return;
        }
        menu._suppressNextClick = false;
        e.stopEvent();
      }, null, { capture: true });
    }
  }
});

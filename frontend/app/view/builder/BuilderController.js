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


Ext.define('yasmine.view.xml.builder.BuilderController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.builder',
  requires: [
    'yasmine.view.xml.builder.parameter.ParameterList',
    'yasmine.view.xml.builder.comparison.Comparison',
    'yasmine.utils.ResponsiveUtil'
  ],
  init: function () {
    this.mon(Ext.ux.Mediator, 'node-selected', this.onTreeItemSelected, this);
  },
  onTreeItemSelected: function(node) {
    this.getViewModel().set('selectedNode', node || null);
  },
  onTreeItemDeSelected: function() {
    this.getViewModel().set('selectedNode', null);
  },
  onShowParameters: function(node) {
    this.getViewModel().set('selectedNode', node);
  },
  afterRender: function () {
    let viewModel = this.getViewModel();
    let xmlId = viewModel.get('xmlId');
    viewModel.set('xml', yasmine.model.Xml.load(parseInt(xmlId)));
    let mode = this.getViewModel().get('viewMode');
    if (mode === yasmine.BuilderMode.BUILDER) {
      this.buildBuilderModeView()
    } else {
      this.buildComparisonModeView()
    }
    this.mon(Ext.GlobalEvents, 'resize', this.onViewportResize, this, {buffer: 200});
    viewModel.set('compactLayout', yasmine.utils.ResponsiveUtil.useStackLayout());
  },
  onExportXmlClick: function () {
    yasmine.store.FileLoader.load(`api/xml/ie/${this.getViewModel().get('xmlId')}`);
  },
  onValidateXmlClick: function () {
    Ext.Ajax.request({
      url: `/api/xml/validate/${this.getViewModel().get('xmlId')}`,
      method: 'GET',
      success: function (response) {
        var payload = JSON.parse(response.responseText);
        var errors = [];
        var warnings = [];

        // Keep compatibility with older backends which returned string[].
        if (Array.isArray(payload)) {
          errors = payload.map(function (message) {
            return {message: message};
          });
        } else {
          errors = payload.errors || [];
          warnings = payload.warnings || [];
        }

        var renderIssues = function (issues) {
          return issues.map(function (issue) {
            var path = issue.path && issue.path !== '/' ?
              '<code>' + Ext.String.htmlEncode(issue.path) + '</code>: ' : '';
            return path + Ext.String.htmlEncode(issue.message || String(issue));
          }).join('<br>');
        };

        var sections = [];
        if (errors.length > 0) {
          sections.push('<b>Errors</b><br>' + renderIssues(errors));
        }
        if (warnings.length > 0) {
          sections.push('<b>Warnings</b><br>' + renderIssues(warnings));
        }
        if (sections.length === 0) {
          sections.push('StationXML 1.2 validation passed with no warnings.');
        }
        Ext.Msg.alert('StationXML 1.2 Validation', sections.join('<br><br>'), Ext.emptyFn);
      }
    });
  },
  onStrictValidateXmlClick: function () {
    var me = this;
    var xmlId = this.getViewModel().get('xmlId');
    me._strictCheckToken = (me._strictCheckToken || 0) + 1;
    me._strictPollFailures = 0;
    var token = me._strictCheckToken;
    me.setStrictCheckProgress(0);
    Ext.Ajax.request({
      url: '/api/xml/validate-strict/' + xmlId,
      method: 'GET',
      timeout: 120000,
      success: function (response) {
        var payload = JSON.parse(response.responseText);
        if (!payload.job_id) {
          Ext.getBody().unmask();
          Ext.Msg.alert('Strict Validate XML', 'Strict XML check could not be started.');
          return;
        }
        me.pollStrictValidation(payload.job_id, token);
      },
      failure: function () {
        me.retryStrictPoll(null, token, 'Strict XML check could not be started.');
      }
    });
  },
  setStrictCheckProgress: function (percent) {
    var text = 'Strict XML check… ' + (parseInt(percent, 10) || 0) + '%';
    var body = Ext.getBody();
    if (!body.isMasked()) {
      body.mask(text);
    }
    var messages = document.querySelectorAll('.x-mask-msg-text');
    var message = messages.length ? messages[messages.length - 1] : null;
    if (message) {
      message.textContent = text;
    }
  },
  pollStrictValidation: function (jobId, token) {
    var me = this;
    if (token !== me._strictCheckToken) {
      return;
    }
    Ext.Ajax.request({
      url: '/api/xml/validate-strict/job/' + jobId + '/',
      method: 'GET',
      timeout: 600000,
      success: function (response) {
        if (token !== me._strictCheckToken) {
          return;
        }
        me._strictPollFailures = 0;
        var payload = JSON.parse(response.responseText);
        me.setStrictCheckProgress(payload.percent || 0);
        if (!payload.done) {
          Ext.defer(function () {
            me.pollStrictValidation(jobId, token);
          }, 400);
          return;
        }
        Ext.getBody().unmask();
        if (payload.failed) {
          Ext.Msg.alert(
            'Strict Validate XML',
            Ext.String.htmlEncode(payload.message || 'Strict XML check failed.')
          );
          return;
        }
        me.showStrictValidationReport(payload);
      },
      failure: function () {
        me.retryStrictPoll(jobId, token, 'Strict XML check failed.');
      }
    });
  },
  retryStrictPoll: function (jobId, token, message) {
    var me = this;
    if (token !== me._strictCheckToken) {
      return;
    }
    me._strictPollFailures = (me._strictPollFailures || 0) + 1;
    if (jobId && me._strictPollFailures < 30) {
      Ext.defer(function () {
        me.pollStrictValidation(jobId, token);
      }, 1000);
      return;
    }
    Ext.getBody().unmask();
    Ext.Msg.alert('Strict Validate XML', Ext.String.htmlEncode(message));
  },
  showStrictValidationReport: function (payload) {
    var issues = payload.issues || ((payload.errors || []).concat(payload.warnings || []));
    var rows = issues.map(function (issue) {
      var category = issue.category;
      if (!category) {
        category = issue.severity === 'error' ? 'schema' : 'recommendation';
      }
      return {
        severity: issue.severity || 'warning',
        category: category,
        path: issue.path && issue.path !== '/' ? issue.path : '',
        message: issue.message || String(issue)
      };
    });
    var warningCount = rows.filter(function (row) { return row.severity !== 'error'; }).length;
    var errorCount = rows.length - warningCount;
    var title = 'Strict XML check — ' + warningCount + ' warning' + (warningCount === 1 ? '' : 's');
    if (errorCount) {
      title += ', ' + errorCount + ' schema error' + (errorCount === 1 ? '' : 's');
    }

    var stageOf = function (message) {
      var match = String(message || '').match(/^(?:Digital\s+)?Stage\s+(\d+)\b/i);
      return match ? match[1] : '';
    };
    var placeOf = function (row) {
      var raw = String(row.path || '').replace(/\s+comment\s+\d+$/i, '').trim();
      var epoch = '';
      var path = raw;
      var epochMatch = raw.match(/^(.*?)\s*\[([^\]]*)\]\s*$/);
      if (epochMatch) {
        path = epochMatch[1].trim();
        epoch = epochMatch[2].trim();
      }
      var parts = path ? path.split('.') : [];
      var network = parts[0] || 'Inventory';
      var station = parts.length > 1 ? parts[1] : '';
      var channel = '';
      if (parts.length >= 4) {
        channel = (parts[2] ? parts[2] + '.' : '') + parts.slice(3).join('.');
      } else if (parts.length === 3) {
        channel = parts[2];
      }
      return {
        network: network,
        station: station,
        epoch: epoch,
        channel: channel,
        stage: channel ? stageOf(row.message) : ''
      };
    };
    var compareKeys = function (left, right) {
      var leftStage = left.match(/^stage-(\d+)$/);
      var rightStage = right.match(/^stage-(\d+)$/);
      if (leftStage && rightStage) {
        return Number(leftStage[1]) - Number(rightStage[1]);
      }
      return left.localeCompare(right);
    };
    var countLeaves = function (nodes) {
      return nodes.reduce(function (total, node) {
        return total + (node.leaf ? 1 : countLeaves(node.children || []));
      }, 0);
    };
    var buildTree = function (sourceRows) {
      var networks = {};
      var ensure = function (map, key, text) {
        if (!map[key]) {
          map[key] = {text: text, childrenMap: {}, leaves: []};
        }
        return map[key];
      };
      sourceRows.forEach(function (row) {
        var place = placeOf(row);
        var node = ensure(networks, place.network, place.network);
        if (place.station) {
          node = ensure(node.childrenMap, place.station, place.station);
        }
        if (place.epoch) {
          node = ensure(node.childrenMap, 'epoch-' + place.epoch, place.epoch);
        }
        if (place.channel) {
          node = ensure(node.childrenMap, place.channel, place.channel);
        }
        if (place.stage) {
          node = ensure(node.childrenMap, 'stage-' + place.stage, 'Stage ' + place.stage);
        }
        node.leaves.push(row);
      });
      var toNodes = function (map) {
        return Object.keys(map).sort(compareKeys).map(function (key) {
          var node = map[key];
          var children = toNodes(node.childrenMap).concat(node.leaves.map(function (row) {
            return {
              text: row.message,
              leaf: true,
              category: row.category,
              path: row.path,
              iconCls: 'x-tree-icon-leaf'
            };
          }));
          return {
            text: node.text + ' (' + countLeaves(children) + ')',
            expanded: false,
            category: '',
            children: children
          };
        });
      };
      return toNodes(networks);
    };
    var rowMatches = function (row, query) {
      return [row.category, row.path, row.message].join(' ').toLowerCase().indexOf(query) >= 0;
    };

    var listStore = Ext.create('Ext.data.Store', {
      fields: ['severity', 'category', 'path', 'message'],
      data: rows
    });
    var treeStore = Ext.create('Ext.data.TreeStore', {
      root: {
        expanded: true,
        children: buildTree(rows)
      }
    });
    var card;
    var treePanel;
    var applyFilter = function (value) {
      var query = (value || '').toLowerCase();
      listStore.clearFilter();
      if (query) {
        listStore.filterBy(function (record) {
          return rowMatches(record.data, query);
        });
      }
      treeStore.setRoot({
        expanded: true,
        children: buildTree(query ? rows.filter(function (row) {
          return rowMatches(row, query);
        }) : rows)
      });
      if (query && treePanel) {
        treePanel.expandAll();
      }
    };

    var report = Ext.create('Ext.container.Container', {
      layout: {
        type: 'vbox',
        align: 'stretch'
      },
      items: [{
        xtype: 'container',
        layout: {
          type: 'hbox',
          align: 'middle'
        },
        padding: '8 8 6 8',
        items: [{
          xtype: 'textfield',
          emptyText: 'Filter',
          width: 260,
          listeners: {
            change: function (field, value) {
              applyFilter(value);
            }
          }
        }, {
          xtype: 'segmentedbutton',
          margin: '0 0 0 8',
          allowDepress: false,
          items: [{
            text: 'List',
            pressed: true
          }, {
            text: 'Tree'
          }],
          listeners: {
            toggle: function (segmented, button, pressed) {
              if (!pressed || !card) {
                return;
              }
              card.setActiveItem(button.text === 'Tree' ? 1 : 0);
            }
          }
        }]
      }, {
        xtype: 'container',
        flex: 1,
        layout: 'card',
        activeItem: 0,
        items: [{
          xtype: 'grid',
          store: listStore,
          bufferedRenderer: false,
          columns: [{
            text: 'Category',
            dataIndex: 'category',
            width: 120
          }, {
            text: 'Path',
            dataIndex: 'path',
            width: 200
          }, {
            text: 'Message',
            dataIndex: 'message',
            flex: 1,
            cellWrap: true
          }],
          viewConfig: {
            enableTextSelection: true,
            // ExtJS 6.2.0 EXTJS-22715: enableTextSelection alone fails inside Window.
            getRowClass: function () {
              return this.enableTextSelection ? 'x-selectable' : '';
            },
            variableRowHeight: true,
            emptyText: 'No warnings.'
          }
        }, {
          xtype: 'treepanel',
          store: treeStore,
          useArrows: true,
          rootVisible: false,
          animate: false,
          bufferedRenderer: false,
          columns: [{
            xtype: 'treecolumn',
            text: 'Network / station / epoch / channel / stage',
            dataIndex: 'text',
            flex: 1,
            cellWrap: true
          }, {
            text: 'Category',
            dataIndex: 'category',
            width: 120
          }],
          viewConfig: {
            enableTextSelection: true,
            // ExtJS 6.2.0 EXTJS-22715: enableTextSelection alone fails inside Window.
            getRowClass: function () {
              return this.enableTextSelection ? 'x-selectable' : '';
            },
            variableRowHeight: true,
            emptyText: 'No warnings.'
          }
        }]
      }]
    });
    card = report.items.getAt(1);
    treePanel = card.items.getAt(1);
    Ext.create('Ext.window.Window', {
      title: title,
      modal: true,
      maximizable: true,
      resizable: true,
      width: Math.min(980, Ext.getBody().getViewSize().width - 40),
      height: Math.min(580, Ext.getBody().getViewSize().height - 40),
      layout: 'fit',
      items: [report]
    }).show();
  },
  buildBuilderModeView: function () {
    this.getViewModel().set('viewMode', yasmine.BuilderMode.BUILDER);
    this.removeModeView('xml-comparison');
    this.createModeView('parameter-list', true);
  },
  buildComparisonModeView: function () {
    this.getViewModel().set('viewMode', yasmine.BuilderMode.COMPARATOR);
    this.removeModeView('parameter-list');
    this.createModeView('xml-comparison', false);
  },
  removeModeView: function (viewName) {
    let view = this.lookup(viewName);
    if (view && view.ownerCt) {
      view.ownerCt.remove(view, true);
    }
  },
  createModeView: function (viewName, isBuilder) {
    let useCard = yasmine.utils.ResponsiveUtil.useCardLayout();
    let cfg = {
      xtype: viewName,
      reference: viewName,
      border: true,
      region: 'east',
      split: !useCard,
      collapsible: !useCard,
      floatable: false,
      hidden: useCard
    };
    // Parameters title / collapse are redundant next to the Hierarchy|Parameters switcher.
    if (isBuilder && useCard) {
      cfg.hideTitle = true;
    }
    if (!useCard) {
      cfg.width = this.getSplitWidth(isBuilder);
    }
    let modeView = Ext.create(cfg);
    this.installModeView(modeView, useCard, isBuilder);
    this.updatePaneSwitcher(!isBuilder);
    let selectedNode = this.getViewModel().get('selectedNode');
    let modeController = modeView.getController && modeView.getController();
    if (selectedNode && modeController && modeController.initData) {
      modeController.initData(selectedNode);
    } else if (selectedNode) {
      Ext.ux.Mediator.fireEvent('node-selected', selectedNode);
    }
  },
  getSplitWidth: function (isBuilder) {
    let viewWidth = this.getView().getWidth() || yasmine.utils.ResponsiveUtil.getWidth();
    let percent = parseFloat(yasmine.utils.ResponsiveUtil.getSplitPercent(isBuilder)) / 100;
    let width = Math.max(280, Math.round(viewWidth * percent));
    let maxWidth = yasmine.utils.ResponsiveUtil.getEastMaxWidth(isBuilder);
    if (maxWidth) {
      width = Math.min(width, maxWidth);
    }
    return width;
  },
  clearBorderSplitters: function () {
    let owner = this.getView();
    if (!owner || owner.destroyed || !owner.query) {
      return;
    }
    Ext.Array.each(owner.query('splitter'), function (splitter) {
      if (splitter && !splitter.destroyed) {
        Ext.destroy(splitter);
      }
    });
  },
  setPaneRenderedHidden: function (pane, hidden) {
    if (!pane || pane.destroyed) {
      return;
    }
    if (hidden) {
      if (pane.hidden) {
        pane.hidden = false;
      }
      pane.hide();
      if (pane.el && pane.el.dom) {
        pane.el.setDisplayed(false);
        pane.el.setStyle({
          display: 'none',
          visibility: 'hidden'
        });
      }
    } else {
      if (pane.el && pane.el.dom) {
        pane.el.setStyle({
          display: '',
          visibility: ''
        });
        pane.el.setDisplayed(true);
      }
      pane.show();
    }
  },
  installModeView: function (modeView, useCard, isBuilder) {
    let owner = this.getView();
    this._usingCard = useCard;
    this.clearBorderSplitters();
    if (modeView.ownerCt === owner) {
      owner.remove(modeView, false);
    }
    modeView.region = 'east';
    modeView.split = !useCard;
    modeView.collapsible = !useCard;
    modeView.floatable = false;
    // Add visible, then hide — hide() is a no-op if hidden is already true,
    // which left the east panel painted over the tree after resize.
    modeView.hidden = false;
    if (useCard) {
      modeView.width = owner.getWidth() || yasmine.utils.ResponsiveUtil.getWidth();
    } else {
      modeView.width = this.getSplitWidth(isBuilder);
    }
    owner.add(modeView);
    if (modeView.setCollapsible) {
      modeView.setCollapsible(!useCard);
    }
    if (useCard) {
      this.setPaneRenderedHidden(modeView, true);
    } else {
      this.setPaneRenderedHidden(modeView, false);
      this.applySplitSizing(modeView, isBuilder);
    }
    if (owner && owner.updateLayout) {
      owner.updateLayout();
    }
  },
  applySplitSizing: function (modeView, isBuilder) {
    let width = this.getSplitWidth(isBuilder);
    let maxWidth = yasmine.utils.ResponsiveUtil.getEastMaxWidth(isBuilder);
    if (maxWidth) {
      modeView.setMaxWidth(maxWidth);
    } else if (modeView.setMaxWidth) {
      modeView.setMaxWidth(undefined);
    }
    modeView.setWidth(width);
  },
  updatePaneSwitcher: function (isComparison) {
    let switcher = this.lookup('builderPaneSwitcher');
    let detailBtn = this.lookup('builderPaneDetailBtn');
    let children = this.lookup('builderChildren');
    let isBuilder = this.getViewModel().get('viewMode') === yasmine.BuilderMode.BUILDER;
    let modeView = this.lookup(isBuilder ? 'parameter-list' : 'xml-comparison');
    let showDetail;
    if (!switcher) {
      return;
    }
    if (this._usingCard) {
      switcher.show();
      if (detailBtn) {
        detailBtn.setText(isComparison ? 'Compare' : 'Parameters');
      }
      // Keep Compare visible when shrinking Comparison Mode instead of
      // resetting to an empty Hierarchy pane.
      showDetail = !!isComparison;
      this._cardShowDetail = showDetail;
      switcher.items.each(function (btn) {
        btn.setPressed(btn.getItemId() === (showDetail ? 'detail' : 'hierarchy'));
      });
      this.showCardPane(showDetail);
      Ext.defer(function () {
        yasmine.utils.ResponsiveUtil.syncWrappingToolbars();
      }, 30);
    } else {
      this._cardShowDetail = null;
      switcher.hide();
      this.setPaneRenderedHidden(children, false);
      this.setPaneRenderedHidden(modeView, false);
    }
  },
  showCardPane: function (showDetail) {
    let children = this.lookup('builderChildren');
    let isBuilder = this.getViewModel().get('viewMode') === yasmine.BuilderMode.BUILDER;
    let modeView = this.lookup(isBuilder ? 'parameter-list' : 'xml-comparison');
    let owner = this.getView();
    this.setPaneRenderedHidden(children, showDetail);
    if (modeView) {
      if (modeView.setCollapsible) {
        modeView.setCollapsible(false);
      }
      this.setPaneRenderedHidden(modeView, !showDetail);
      if (showDetail) {
        modeView.setWidth(owner.getWidth());
      }
    }
    if (owner && owner.updateLayout) {
      owner.updateLayout();
    }
    if (showDetail && modeView && modeView.getController && modeView.getController() &&
        modeView.getController().syncComparisonSplit) {
      modeView.getController().syncComparisonSplit();
    }
  },
  onBuilderPaneToggle: function (container, button, pressed) {
    if (!pressed || !this._usingCard) {
      return;
    }
    this._cardShowDetail = button.getItemId() === 'detail';
    this.showCardPane(this._cardShowDetail);
  },
  onViewportResize: function () {
    this.getViewModel().set('compactLayout', yasmine.utils.ResponsiveUtil.useStackLayout());
    let isBuilder = this.getViewModel().get('viewMode') === yasmine.BuilderMode.BUILDER;
    let viewName = isBuilder ? 'parameter-list' : 'xml-comparison';
    let modeView = this.lookup(viewName);
    let wantCard;
    let comparison;
    if (!modeView) {
      return;
    }
    wantCard = yasmine.utils.ResponsiveUtil.useCardLayout();
    if (wantCard === this._usingCard) {
      if (!wantCard) {
        this.applySplitSizing(modeView, isBuilder);
      } else if (!modeView.isHidden()) {
        modeView.setWidth(this.getView().getWidth());
      }
      if (this.getView() && this.getView().updateLayout) {
        this.getView().updateLayout();
      }
      comparison = this.lookup('xml-comparison');
      if (comparison && comparison.getController && comparison.getController()) {
        comparison.getController().syncComparisonSplit();
      }
      return;
    }
    // Rebuild Parameters so hideTitle / header chrome match card vs split layout.
    if (isBuilder) {
      this.removeModeView(viewName);
      this.createModeView(viewName, true);
      return;
    }
    this.installModeView(modeView, wantCard, isBuilder);
    this.updatePaneSwitcher(!isBuilder);
    comparison = this.lookup('xml-comparison');
    if (comparison && comparison.getController && comparison.getController()) {
      comparison.getController().syncComparisonSplit();
    }
  }
});

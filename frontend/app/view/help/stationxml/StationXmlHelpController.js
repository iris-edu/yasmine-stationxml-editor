/* 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov */
Ext.define('yasmine.view.help.stationxml.StationXmlHelpController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.stationxml-help',

  requires: [
    'yasmine.utils.StationXmlHelpContext'
  ],

  loadContext: function (context, title) {
    var view = this.getView();
    this.pendingContext = context;
    this.pendingSearch = context && context.search ? context.search : '';
    if (title) {
      view.setTitle('StationXML 1.2: ' + title);
    }
    view.setLoading('Loading StationXML 1.2 schema…');
    yasmine.utils.StationXmlHelpContext.load(
      this.onCatalogLoaded,
      this.onCatalogError,
      this
    );
  },

  onCatalogLoaded: function (catalog) {
    this.catalog = catalog;
    this.originalRoot = this.toTreeNode(catalog.tree);
    this.applyTree(this.originalRoot);
    this.getView().setLoading(false);

    var path = yasmine.utils.StationXmlHelpContext.resolve(
      this.pendingContext,
      catalog
    );
    this.showPath(path || catalog.rootPath);
    this.applyPendingSearch(path || catalog.rootPath);
  },

  applyPendingSearch: function (preferredPath) {
    var searchField = this.lookupReference('searchField');
    var query = this.pendingSearch || '';
    if (!searchField) {
      return;
    }
    searchField.suspendEvent('change');
    searchField.setValue(query);
    searchField.resumeEvent('change');
    if (query) {
      this.applySearch(query, preferredPath);
    }
  },

  onCatalogError: function () {
    this.getView().setLoading(false);
    this.lookupReference('detailPanel').update(
      '<div class="stationxml-help-error">' +
      'StationXML 1.2 help could not be loaded.</div>'
    );
  },

  toTreeNode: function (node) {
    var me = this;
    var children = [];
    Ext.Array.each(node.attributes || [], function (attribute) {
      children.push(Ext.apply({}, attribute, {
        text: '@' + attribute.xmlName,
        leaf: true,
        iconCls: 'x-fa fa-at'
      }));
    });
    Ext.Array.each(node.children || [], function (child) {
      children.push(me.toTreeNode(child));
    });
    return {
      text: node.xmlName,
      xmlName: node.xmlName,
      path: node.path,
      kind: node.kind,
      expanded: node.path === '/FDSNStationXML',
      leaf: children.length === 0,
      iconCls: 'x-fa fa-code',
      children: children
    };
  },

  applyTree: function (root) {
    var tree = this.lookupReference('schemaTree');
    tree.setStore(Ext.create('Ext.data.TreeStore', {
      root: Ext.clone(root)
    }));
  },

  onTreeSelect: function (tree, record) {
    var path = record && record.get('path');
    if (path) {
      this.showPath(path, false);
    }
  },

  showPath: function (path, selectTree) {
    if (!this.catalog) {
      this.pendingContext = path;
      return;
    }
    path = yasmine.utils.StationXmlHelpContext.nearestKnownPath(
      path,
      this.catalog
    );
    var entry = this.catalog.nodes[path];
    if (!entry) {
      return;
    }
    this.getViewModel().set('currentPath', path);
    this.lookupReference('detailPanel').update(this.renderEntry(entry));

    if (selectTree !== false) {
      var tree = this.lookupReference('schemaTree');
      var record = tree.getStore().findNode(
        'path',
        path,
        tree.getStore().getRoot(),
        true,
        false,
        true
      );
      if (record) {
        var parent = record.parentNode;
        while (parent) {
          parent.expand();
          parent = parent.parentNode;
        }
        tree.setSelection(record);
      }
    }
  },

  encode: function (value) {
    return Ext.String.htmlEncode(String(value == null ? '' : value));
  },

  renderEntry: function (entry) {
    var me = this;
    var docs = entry.documentation || {};
    var html = [];
    var kindLabel = entry.kind === 'attribute' ?
      'XML attribute' : 'XML element';

    html.push('<article class="stationxml-help-entry x-selectable">');
    html.push('<div class="stationxml-help-kind">' + kindLabel + '</div>');
    html.push('<h2><code>' +
      (entry.kind === 'attribute' ? '@' : '') +
      me.encode(entry.xmlName) + '</code></h2>');
    html.push('<div class="stationxml-help-path"><b>Schema path:</b> ' +
      '<code>' + me.encode(entry.path) + '</code></div>');

    html.push('<dl class="stationxml-help-facts">');
    if (entry.declaredType || entry.primitiveType) {
      html.push('<dt>Type</dt><dd>' +
        me.encode(entry.declaredType || entry.primitiveType) + '</dd>');
    }
    if (entry.kind === 'attribute') {
      html.push('<dt>Use</dt><dd>' +
        me.encode(entry.use || 'optional') + '</dd>');
    } else if (entry.effectiveOccurs) {
      var max = entry.effectiveOccurs.max == null ?
        'unbounded' : entry.effectiveOccurs.max;
      html.push('<dt>Cardinality</dt><dd>' +
        me.encode(entry.effectiveOccurs.min + '..' + max) + '</dd>');
    }
    if (entry.default != null) {
      html.push('<dt>Default</dt><dd><code>' +
        me.encode(entry.default) + '</code></dd>');
    }
    if (entry.fixed != null) {
      html.push('<dt>Fixed</dt><dd><code>' +
        me.encode(entry.fixed) + '</code></dd>');
    }
    html.push('</dl>');

    Ext.Array.each(docs.description || [], function (paragraph) {
      html.push('<p>' + me.encode(paragraph) + '</p>');
    });
    if (!(docs.description || []).length) {
      html.push('<p class="stationxml-help-empty">' +
        'The StationXML 1.2 XSD does not provide a prose description.' +
        '</p>');
    }

    if (entry.facets && Ext.Object.getSize(entry.facets)) {
      html.push('<h3>Constraints</h3><ul>');
      Ext.Object.each(entry.facets, function (name, value) {
        var display = Ext.isArray(value) ? value.join(', ') : value;
        html.push('<li><b>' + me.encode(name) + ':</b> <code>' +
          me.encode(display) + '</code></li>');
      });
      html.push('</ul>');
    }

    if ((entry.conditions || []).length) {
      html.push('<h3>Conditional structure</h3><ul>');
      Ext.Array.each(entry.conditions, function (condition) {
        html.push('<li>' + me.encode(
          condition.kind === 'choice' ?
            'This entry belongs to an exclusive choice.' :
            'This entry belongs to the ' + condition.name + ' group.'
        ) + '</li>');
      });
      html.push('</ul>');
    }

    if ((docs.warnings || []).length) {
      html.push('<h3>Warnings</h3>');
      Ext.Array.each(docs.warnings, function (warning) {
        html.push('<div class="stationxml-help-warning">' +
          me.encode(warning) + '</div>');
      });
    }

    if ((docs.examples || []).length) {
      html.push('<h3>Examples</h3>');
      Ext.Array.each(docs.examples, function (example) {
        html.push('<pre>' + me.encode(example) + '</pre>');
      });
    }

    me.renderLinks(html, 'Attributes', entry.attributes);
    me.renderLinks(html, 'Child elements', entry.children);

    html.push('<footer>Source: FDSN StationXML 1.2 XSD. ' +
      '<a href="https://docs.fdsn.org/projects/stationxml/en/v1.2/" ' +
      'target="_blank" rel="noopener">Official documentation</a>' +
      '</footer>');
    html.push('</article>');
    return html.join('');
  },

  renderLinks: function (html, title, paths) {
    var me = this;
    if (!paths || !paths.length) {
      return;
    }
    html.push('<h3>' + me.encode(title) + '</h3><ul>');
    Ext.Array.each(paths, function (path) {
      var entry = me.catalog.nodes[path];
      if (!entry) {
        return;
      }
      html.push('<li><a href="#" data-stationxml-help-path="' +
        me.encode(path) + '"><code>' +
        (entry.kind === 'attribute' ? '@' : '') +
        me.encode(entry.xmlName) + '</code></a></li>');
    });
    html.push('</ul>');
  },

  onDetailAfterRender: function (panel) {
    if (panel.body && panel.body.selectable) {
      panel.body.selectable();
    }
    panel.getEl().on('click', function (event, target) {
      var link = Ext.fly(target).findParent(
        '[data-stationxml-help-path]',
        panel.getEl(),
        true
      );
      if (!link) {
        return;
      }
      event.preventDefault();
      this.showPath(link.getAttribute('data-stationxml-help-path'));
    }, this);
  },

  onSearchChange: function (field, value) {
    if (!this.catalog) {
      return;
    }
    var query = String(value || '').trim();
    if (!query) {
      this.applyTree(this.originalRoot);
      this.showPath(
        this.getViewModel().get('currentPath') || this.catalog.rootPath
      );
      return;
    }
    this.applySearch(query, this.getViewModel().get('currentPath'));
  },

  applySearch: function (query, preferredPath) {
    var helper = yasmine.utils.StationXmlHelpContext;
    var scored = [];
    Ext.Object.each(this.catalog.nodes, function (path, entry) {
      var score = helper.searchScore(entry, query);
      if (score) {
        scored.push({
          path: path,
          entry: entry,
          score: score
        });
      }
    });
    scored.sort(function (left, right) {
      return right.score - left.score;
    });
    scored = scored.slice(0, 200);
    this.applyTree({
      text: 'Search results (' + scored.length + ')',
      xmlName: 'Search results',
      path: null,
      kind: 'search',
      expanded: true,
      leaf: false,
      children: Ext.Array.map(scored, function (item) {
        var entry = item.entry;
        return {
          text: (entry.kind === 'attribute' ? '@' : '') + entry.xmlName +
            ' — ' + item.path,
          xmlName: entry.xmlName,
          path: item.path,
          kind: entry.kind,
          leaf: true,
          iconCls: entry.kind === 'attribute' ?
            'x-fa fa-at' : 'x-fa fa-code'
        };
      })
    });
    if (preferredPath && Ext.Array.some(scored, function (item) {
      return item.path === preferredPath;
    })) {
      this.showPath(preferredPath);
    }
  },

  onFullSchemaClick: function () {
    if (!this.catalog) {
      return;
    }
    this.lookupReference('searchField').setValue('');
    this.applyTree(this.originalRoot);
    this.showPath(this.catalog.rootPath);
  }
});

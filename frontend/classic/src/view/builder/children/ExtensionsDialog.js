/* 2026-09-29, version 4.4.0-beta: ASGSR, Alexey Emanov
 *
 * Read-only foreign-namespace extensions for a Hierarchy node.
 */

Ext.define('yasmine.view.xml.builder.children.ExtensionsDialog', {
  extend: 'Ext.window.Window',
  xtype: 'node-extensions-dialog',
  title: 'Extensions (foreign namespace)',
  modal: true,
  width: 560,
  maxHeight: 480,
  layout: 'fit',
  cls: 'yasmine-window',
  closeAction: 'destroy',
  bodyPadding: 12,
  scrollable: true,

  config: {
    summary: null
  },

  initComponent: function () {
    var summary = this.getSummary() || {};
    var nodes = summary.nodes || [];
    var lines = [
      '<p style="margin:0 0 10px 0;">Foreign-namespace elements and attributes are stored as opaque sidecars. They are read-only here and are removed when you delete the parent node.</p>'
    ];
    if (!nodes.length) {
      lines.push('<p style="margin:0;color:#555;">No extension sidecars on this node or its children.</p>');
    } else {
      lines.push(
        '<p style="margin:0 0 10px 0;"><b>' +
        Ext.htmlEncode(String(summary.sidecarNodeCount || 0)) +
        '</b> node(s) with sidecars — ' +
        Ext.htmlEncode(String(summary.elementCount || 0)) +
        ' element(s), ' +
        Ext.htmlEncode(String(summary.attributeCount || 0)) +
        ' attribute(s).</p>'
      );
      nodes.forEach(function (row) {
        lines.push(
          '<div style="margin:0 0 8px 0;padding:6px 8px;border:1px solid #ddd;">' +
          '<div><b>' + Ext.htmlEncode(row.code || ('#' + row.id)) + '</b></div>' +
          '<div style="color:#555;font-size:12px;">elements: ' +
          Ext.htmlEncode((row.elements || []).join(', ') || '—') +
          '</div>' +
          '<div style="color:#555;font-size:12px;">attributes: ' +
          Ext.htmlEncode((row.attributes || []).join(', ') || '—') +
          '</div></div>'
        );
      });
    }
    this.items = [{
      xtype: 'component',
      html: lines.join('')
    }];
    this.buttons = [{
      text: 'Close',
      handler: function (btn) {
        btn.up('window').close();
      }
    }];
    this.callParent(arguments);
  }
});

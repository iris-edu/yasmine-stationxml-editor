# 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
# Response parameter editor must fill the window and open the tree.

import json
import os
import time
import unittest

from yasmine.app.tests.common import check_web_app_is_down, skip_unless_gui
from yasmine.app.tests.common.wgui import SeletiounTestMixin


OPEN_EDITOR_JS = """
return (function () {
    try {
        Ext.ComponentQuery.query('parameter-editor').forEach(function (win) {
            if (win.destroy) { win.destroy(); }
        });
        var record = Ext.create('yasmine.model.Parameter');
        record.set('name', 'response');
        record.set('class', 'yasmine-channel-response-field');
        record.set('value', {nodeId: 1, response: {Response: {}}});
        record.set('nodeId', 1);
        var EditorCtl = Ext.ClassManager.get(
            'yasmine.view.xml.builder.parameter.items.channelresponse.ChannelResponseEditorController'
        );
        var proto = EditorCtl && EditorCtl.prototype;
        var originalPlot = proto && proto.loadChannelResponsePlot;
        if (proto) {
            proto.loadChannelResponsePlot = Ext.emptyFn;
        }
        var win = Ext.create({
            xtype: 'parameter-editor',
            scrollable: false,
            layout: 'fit'
        });
        win.getViewModel().set('record', record);
        win.getViewModel().set('nodeType', yasmine.NodeTypeEnum.channel);
        try {
            win.getController().createFrom();
            win.show();
        } finally {
            if (proto && originalPlot) {
                proto.loadChannelResponsePlot = originalPlot;
            }
        }
        return {ok: true};
    } catch (error) {
        return {
            ok: false,
            error: String((error && error.message) || error),
            stack: error && error.stack
        };
    }
})();
"""

GEOMETRY_JS = """
return (function () {
    function safeCall(obj, method, fallback) {
        try {
            if (!obj || typeof obj[method] !== 'function') { return fallback; }
            return obj[method]();
        } catch (error) {
            return fallback;
        }
    }
    function box(cmp) {
        if (!cmp) { return null; }
        var layout = null;
        try {
            layout = cmp.getLayout && cmp.getLayout() ? cmp.getLayout().type : null;
        } catch (error) {
            layout = String(error);
        }
        return {
            xtype: safeCall(cmp, 'getXType', null),
            width: safeCall(cmp, 'getWidth', null),
            height: safeCall(cmp, 'getHeight', null),
            hidden: safeCall(cmp, 'isHidden', null),
            layout: layout,
            itemCount: cmp.items && cmp.items.getCount ? cmp.items.getCount() : 0,
            text: cmp.el && cmp.el.dom ? String(cmp.el.dom.innerText || '').slice(0, 240) : ''
        };
    }
    function bodyBox(win) {
        try {
            if (!win || !win.body) { return null; }
            return {
                width: win.body.getWidth ? win.body.getWidth(true) : null,
                height: win.body.getHeight ? win.body.getHeight(true) : null
            };
        } catch (error) {
            return {error: String(error)};
        }
    }
    try {
        var win = Ext.ComponentQuery.query('parameter-editor')[0];
        var field = Ext.ComponentQuery.query('yasmine-channel-response-field')[0];
        var preview = Ext.ComponentQuery.query('response-preview')[0];
        var tree = Ext.ComponentQuery.query('channel-response-tree-editor')[0];
        var vm = win && win.getViewModel ? win.getViewModel() : null;
        return {
            win: box(win),
            body: bodyBox(win),
            field: box(field),
            preview: box(preview),
            tree: box(tree),
            flags: vm ? {
                showResponseActions: vm.get('showResponseActions'),
                showEditResponse: vm.get('showEditResponse'),
                showSelectResponse: vm.get('showSelectResponse'),
                showRecalculateSensitivity: vm.get('showRecalculateSensitivity'),
                currentView: field && field.getViewModel ? field.getViewModel().get('currentViewReference') : null
            } : null,
            pageErrors: window.__yasminePageErrors || []
        };
    } catch (error) {
        return {error: String((error && error.message) || error), stack: error && error.stack};
    }
})();
"""

SHOW_CHART_TOOLBAR_JS = """
return (function () {
    try {
        var field = Ext.ComponentQuery.query('yasmine-channel-response-field')[0];
        var chart;
        if (!field || !field.getViewModel) {
            return {ok: false, error: 'no response field'};
        }
        field.getViewModel().set(
            'channelResponseImageUrl',
            'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=='
        );
        chart = Ext.ComponentQuery.query('response-chart')[0];
        if (chart && chart.updateLayout) {
            chart.updateLayout();
        }
        return {ok: true};
    } catch (error) {
        return {ok: false, error: String((error && error.message) || error)};
    }
})();
"""

CHART_TOOLBAR_JS = """
return (function () {
    function box(cmp) {
        if (!cmp) { return null; }
        var el = cmp.getEl && cmp.getEl();
        var region = el && el.getRegion ? el.getRegion() : null;
        return {
            xtype: cmp.getXType && cmp.getXType(),
            hidden: cmp.isHidden && cmp.isHidden(),
            width: cmp.getWidth && cmp.getWidth(),
            height: cmp.getHeight && cmp.getHeight(),
            left: region ? region.left : null,
            right: region ? region.right : null,
            top: region ? region.top : null,
            bottom: region ? region.bottom : null
        };
    }
    try {
        var win = Ext.ComponentQuery.query('parameter-editor')[0];
        var chart = Ext.ComponentQuery.query('response-chart')[0];
        var toolbar = chart && chart.items && chart.items.getAt(0);
        var fields = chart ? chart.query('numberfield') : [];
        var buttons = chart ? chart.query('button') : [];
        var recalculate = win && win.down('button[tooltip=Recalculate Sensitivity]');
        return {
            win: box(win),
            toolbar: box(toolbar),
            minField: box(fields[0]),
            maxField: box(fields[1]),
            rebuild: box(buttons[0]),
            downloadPlot: box(buttons[1]),
            downloadCsv: box(buttons[2]),
            recalculate: box(recalculate)
        };
    } catch (error) {
        return {error: String((error && error.message) || error)};
    }
})();
"""

CLICK_EDIT_JS = """
return (function () {
    try {
        var win = Ext.ComponentQuery.query('parameter-editor')[0];
        if (!win) { return {ok: false, error: 'no window'}; }
        win.getController().onEditResponseClick();
        return {ok: true};
    } catch (error) {
        return {
            ok: false,
            error: String((error && error.message) || error),
            stack: error && error.stack
        };
    }
})();
"""


@skip_unless_gui
@unittest.skipIf(check_web_app_is_down(), "Application is down")
class ResponseEditorGuiTest(SeletiounTestMixin):

    SIZES = (
        (1440, 900, 'xl'),
        (375, 812, 'sm-phone'),
        (768, 1024, 'sm-tablet'),
        (1920, 1080, 'xxl-wide'),
    )

    def test_response_tree_reselection_uses_sibling_ordinals(self):
        self.open_page('#xmls')
        result = self.driver.execute_script("""
            return (function () {
                var controller;
                var initialStore;
                var rebuiltStore;
                try {
                    var Controller = Ext.ClassManager.get(
                        'yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.' +
                        'ChannelResponseTreeEditorController'
                    );
                    if (!Controller) {
                        throw new Error('Response tree controller is not loaded');
                    }
                    function responseTreeData() {
                        return {
                            key: 'Response',
                            Response: {},
                            expanded: true,
                            children: [
                                {
                                    key: 'Stage',
                                    expanded: true,
                                    children: [
                                        {key: 'Pole', leaf: true},
                                        {key: 'Pole', leaf: true}
                                    ]
                                },
                                {
                                    key: 'Stage',
                                    expanded: true,
                                    children: [
                                        {key: 'Pole', leaf: true},
                                        {key: 'Pole', leaf: true}
                                    ]
                                }
                            ]
                        };
                    }

                    initialStore = Ext.create('Ext.data.TreeStore', {
                        root: responseTreeData()
                    });
                    var initiallySelected =
                        initialStore.getRoot().childNodes[1].childNodes[1];
                    var tree = {
                        store: initialStore,
                        selection: [initiallySelected],
                        getSelection: function () {
                            return this.selection;
                        },
                        setSelection: function (record) {
                            this.selection = [record];
                        },
                        setStore: function (store) {
                            this.store = store;
                            rebuiltStore = store;
                        }
                    };

                    controller = new Controller();
                    controller.getViewModel = function () {
                        return {set: Ext.emptyFn};
                    };
                    controller.lookupReference = function (reference) {
                        return reference === 'channelresponsetree' ? tree : null;
                    };
                    controller.convertResponseTreeStore = Ext.emptyFn;
                    controller.onNodeSelected = Ext.emptyFn;

                    var selectedPath =
                        controller.buildNodeIdentityPath(initiallySelected);
                    controller.reloadTree(responseTreeData());
                    var selectedAfterReload = tree.getSelection()[0];

                    return {
                        ok: true,
                        path: selectedPath,
                        selectedKey: selectedAfterReload.get('key'),
                        parentKey: selectedAfterReload.parentNode.get('key'),
                        stageOrdinal:
                            rebuiltStore.getRoot().childNodes.indexOf(
                                selectedAfterReload.parentNode
                            ),
                        poleOrdinal:
                            selectedAfterReload.parentNode.childNodes.indexOf(
                                selectedAfterReload
                            )
                    };
                } catch (error) {
                    return {
                        ok: false,
                        error: String((error && error.message) || error),
                        stack: error && error.stack
                    };
                } finally {
                    Ext.destroy(controller, rebuiltStore, initialStore);
                }
            })();
        """)
        self.assertTrue(result.get('ok'), result)
        self.assertEqual(
            result.get('path'),
            [
                {'key': 'Stage', 'ordinal': 1},
                {'key': 'Pole', 'ordinal': 1},
            ],
            result,
        )
        self.assertEqual(result.get('selectedKey'), 'Pole', result)
        self.assertEqual(result.get('parentKey'), 'Stage', result)
        self.assertEqual(result.get('stageOrdinal'), 1, result)
        self.assertEqual(result.get('poleOrdinal'), 1, result)

    def _dismiss_messageboxes(self):
        try:
            self.driver.execute_script(
                "Ext.ComponentQuery.query('messagebox').forEach(function (box) {"
                "  var btn = box.down && box.down('button');"
                "  if (btn && btn.click) { btn.click(); }"
                "  else if (box.hide) { box.hide(); }"
                "});"
            )
        except Exception as error:
            return str(error)
        return None

    def test_response_editor_fills_window_and_opens_tree(self):
        report = []
        self.open_page('#xmls')
        try:
            for width, height, label in self.SIZES:
                row = {'label': label, 'size': [width, height]}
                self.resize_viewport(width, height)
                opened = self.driver.execute_script(OPEN_EDITOR_JS)
                row['open'] = opened
                if not opened.get('ok'):
                    report.append(row)
                    continue
                self.wait_js(
                    "Ext.ComponentQuery.query('parameter-editor').length>0",
                    'parameter-editor missing at %s' % label,
                )
                time.sleep(0.6)
                row['dismissPreview'] = self._dismiss_messageboxes()
                row['preview'] = self.driver.execute_script(GEOMETRY_JS)
                row['previewShot'] = os.path.basename(self.save_screenshot(
                    'response-preview__%s__%sx%s' % (label, width, height)
                ))
                row['click'] = self.driver.execute_script(CLICK_EDIT_JS)
                time.sleep(0.8)
                row['dismissTree'] = self._dismiss_messageboxes()
                row['tree'] = self.driver.execute_script(GEOMETRY_JS)
                row['treeShot'] = os.path.basename(self.save_screenshot(
                    'response-tree__%s__%sx%s' % (label, width, height)
                ))
                report.append(row)
                self.driver.execute_script(
                    "Ext.ComponentQuery.query('parameter-editor').forEach(function (win) {"
                    "  if (win.destroy) { win.destroy(); }"
                    "});"
                )
        finally:
            report_path = os.path.join(self.screenshot_dir(), 'response-editor.json')
            with open(report_path, 'w', encoding='utf-8') as handle:
                json.dump(report, handle, indent=2)

        self.assertTrue(report, 'no response editor samples captured')
        widest = next((row for row in report if row.get('label') == 'xl'), report[-1])
        self.assertTrue(widest.get('open', {}).get('ok'), widest.get('open'))
        self.assertTrue(widest.get('click', {}).get('ok'), widest.get('click'))
        preview_height = (widest['preview'].get('preview') or {}).get('height') or 0
        field_height = (widest['preview'].get('field') or {}).get('height') or 0
        self.assertGreater(
            max(preview_height, field_height),
            80,
            'response preview collapsed: %s' % widest['preview'],
        )
        tree_height = (widest['tree'].get('tree') or {}).get('height') or 0
        self.assertGreater(
            tree_height,
            80,
            'response tree missing/collapsed: %s' % widest['tree'],
        )
        self.assertFalse(
            (widest['tree'].get('flags') or {}).get('showEditResponse'),
            'Edit Response stayed visible after opening the tree',
        )

    def _assert_inside(self, inner, outer, label):
        self.assertIsNotNone(inner, '%s missing' % label)
        self.assertFalse(inner.get('hidden'), '%s hidden: %s' % (label, inner))
        self.assertGreater(inner.get('width') or 0, 20, '%s too narrow: %s' % (label, inner))
        self.assertGreater(inner.get('height') or 0, 16, '%s too short: %s' % (label, inner))
        if outer and inner.get('right') is not None and outer.get('right') is not None:
            self.assertLessEqual(
                inner['right'],
                outer['right'] + 2,
                '%s clipped on the right: %s vs window %s' % (label, inner, outer),
            )
        if outer and inner.get('bottom') is not None and outer.get('bottom') is not None:
            self.assertLessEqual(
                inner['bottom'],
                outer['bottom'] + 2,
                '%s clipped on the bottom: %s vs window %s' % (label, inner, outer),
            )

    def test_response_plot_toolbar_fits_phone(self):
        self.open_page('#xmls')
        self.resize_viewport(375, 812)
        opened = self.driver.execute_script(OPEN_EDITOR_JS)
        self.assertTrue(opened.get('ok'), opened)
        self.wait_js(
            "Ext.ComponentQuery.query('parameter-editor').length>0",
            'parameter-editor missing',
        )
        shown = self.driver.execute_script(SHOW_CHART_TOOLBAR_JS)
        self.assertTrue(shown.get('ok'), shown)
        time.sleep(0.4)
        geometry = self.driver.execute_script(CHART_TOOLBAR_JS)
        self.save_screenshot('response-plot-toolbar__sm-phone__375x812')
        win = geometry.get('win') or {}
        toolbar = geometry.get('toolbar') or {}
        self.assertGreater(
            toolbar.get('height') or 0,
            56,
            'plot toolbar collapsed: %s' % geometry,
        )
        self._assert_inside(geometry.get('minField'), win, 'Min')
        self._assert_inside(geometry.get('maxField'), win, 'Max')
        self._assert_inside(geometry.get('rebuild'), win, 'Rebuild Plot')
        self._assert_inside(geometry.get('recalculate'), win, 'Recalculate')

    def test_nrl_response_type_cards_visible_in_compact_mode(self):
        """NRL Offline/Online type step must show cards in card/compact layout."""
        self.open_page('#xmls')
        self.resize_viewport(500, 700)
        result = self.driver.execute_script("""
            return (function () {
                function region(cmp) {
                    var el = cmp && cmp.getEl && cmp.getEl();
                    var box = el && el.getRegion && el.getRegion();
                    if (!box) { return null; }
                    return {
                        left: box.left, right: box.right,
                        top: box.top, bottom: box.bottom,
                        width: box.right - box.left,
                        height: box.bottom - box.top,
                        hidden: cmp.isHidden && cmp.isHidden()
                    };
                }
                var win;
                try {
                    document.documentElement.classList.add('yasmine-vp-sm');
                    document.body.classList.add('yasmine-vp-sm');
                    win = Ext.create('Ext.window.Window', {
                        title: 'NRL type cards',
                        width: 500,
                        height: 520,
                        modal: true,
                        layout: 'fit',
                        items: [{xtype: 'nrl-response-type-selector', flex: 1}]
                    });
                    win.show();
                    if (win.updateLayout) { win.updateLayout(); }
                    var sel = win.down('nrl-response-type-selector');
                    var buttons = sel ? sel.query('button') : [];
                    var panel = region(sel);
                    var cards = buttons.map(function (btn) {
                        var box = region(btn);
                        var text = (btn.getText && btn.getText()) || '';
                        return {
                            text: String(text).replace(/<br\\s*\\/?>/gi, ' '),
                            box: box,
                            inside: !!(panel && box &&
                                box.top >= panel.top - 2 &&
                                box.bottom <= panel.bottom + 2 &&
                                box.left >= panel.left - 2 &&
                                box.right <= panel.right + 2 &&
                                box.height > 20 && box.width > 40)
                        };
                    });
                    return {
                        ok: true,
                        buttonCount: buttons.length,
                        panel: panel,
                        cards: cards,
                        allInside: cards.length === 3 &&
                            cards.every(function (card) { return card.inside; }),
                        winId: win ? win.getId() : null
                    };
                } catch (error) {
                    return {
                        ok: false,
                        error: String((error && error.message) || error),
                        stack: error && error.stack
                    };
                }
            })();
        """)
        try:
            self.save_screenshot('nrl-response-type-cards__compact__500x700')
            self.assertTrue(result.get('ok'), result)
            self.assertEqual(result.get('buttonCount'), 3, result)
            self.assertTrue(
                result.get('allInside'),
                'response type cards clipped in compact mode: %s' % result,
            )
        finally:
            self.driver.execute_script("""
                document.documentElement.classList.remove('yasmine-vp-sm');
                document.body.classList.remove('yasmine-vp-sm');
                var id = arguments[0];
                var win = id && Ext.getCmp(id);
                if (win) { Ext.destroy(win); }
                Ext.ComponentQuery.query('window[title=NRL type cards]').forEach(function (w) {
                    Ext.destroy(w);
                });
            """, result.get('winId') if isinstance(result, dict) else None)

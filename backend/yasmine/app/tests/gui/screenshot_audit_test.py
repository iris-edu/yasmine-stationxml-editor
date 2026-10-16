# 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
# Capture every main route and key dialog at ResponsiveUtil breakpoints.

import json
import os
import time
import unittest

from yasmine.app.tests.common import check_web_app_is_down, skip_unless_gui
from yasmine.app.tests.common.wgui import SeletiounTestMixin


@skip_unless_gui
@unittest.skipIf(check_web_app_is_down(), "Application is down")
class ScreenshotAuditGuiTest(SeletiounTestMixin):

    # Mirrors frontend/app/utils/ResponsiveUtil.js
    SIZES = (
        (320, 640, 'xs'),
        (375, 812, 'sm-phone'),
        (767, 500, 'stack-compact'),
        (768, 1024, 'sm-tablet'),
        (1024, 768, 'md'),
        (1279, 800, 'lg-top-header'),
        (1280, 800, 'lg-left-header'),
        (1440, 900, 'xl'),
        (1920, 1080, 'xxl-wide'),
        (2560, 1440, 'uw'),
    )
    ROUTES = (
        ('xmls', 'xml-list'),
        ('settings', 'settings-list'),
        ('user-libraries', 'userlibrary-list'),
        ('about', 'app-main'),
    )
    DIALOGS = (
        ('xml-import', None),
        ('xml-edit', None),
        ('wizard-create', None),
        ('stationxml-help', None),
        ('main_help', None),
        ('measurement-metadata-window', None),
    )

    LAYOUT_JS = """
        return (function () {
            var vw = window.innerWidth;
            var vh = window.innerHeight;
            var overflow = document.documentElement.scrollWidth - vw;
            var clipped = [];
            var overlapping = [];
            if (window.yasmine && yasmine.utils && yasmine.utils.ResponsiveUtil) {
                yasmine.utils.ResponsiveUtil.syncWrappingToolbars();
                yasmine.utils.ResponsiveUtil.clampVisibleWindows();
            }
            var query = 'button:visible';
            var items = (window.Ext && Ext.ComponentQuery)
                ? Ext.ComponentQuery.query(query) : [];
            var boxes = [];
            var activeWin = window.Ext && Ext.WindowManager && Ext.WindowManager.getActive
                ? Ext.WindowManager.getActive() : null;
            function layerId(cmp) {
                var win = cmp.up && cmp.up('window');
                return win ? win.id : 'page';
            }
            function containsBox(outer, inner) {
                return inner.x >= outer.x - 2 &&
                    inner.y >= outer.y - 2 &&
                    inner.x + inner.w <= outer.x + outer.w + 2 &&
                    inner.y + inner.h <= outer.y + outer.h + 2;
            }
            function overlapArea(a, b) {
                var w = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x);
                var h = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
                return (w > 0 && h > 0) ? w * h : 0;
            }
            items.forEach(function (cmp) {
                var win;
                var box;
                var info;
                if (!cmp.getBox || !cmp.isVisible || !cmp.isVisible(true)) {
                    return;
                }
                win = cmp.up && cmp.up('window');
                if (activeWin && !activeWin.destroyed) {
                    if (!win || win.id !== activeWin.id) {
                        return;
                    }
                } else if (win) {
                    return;
                }
                box = cmp.getBox();
                if (!box || box.width < 2 || box.height < 2) {
                    return;
                }
                var node = cmp.el && cmp.el.dom;
                var viewLeft = 0;
                var viewTop = 0;
                var viewRight = vw;
                var viewBottom = vh;
                while (node && node !== document.body) {
                    var style = window.getComputedStyle(node);
                    var clipsY = /(auto|scroll|hidden)/.test(style.overflowY);
                    var clipsX = /(auto|scroll|hidden)/.test(style.overflowX);
                    if (clipsX || clipsY) {
                        var rect = node.getBoundingClientRect();
                        if (clipsX) {
                            viewLeft = Math.max(viewLeft, rect.left);
                            viewRight = Math.min(viewRight, rect.right);
                        }
                        if (clipsY) {
                            viewTop = Math.max(viewTop, rect.top);
                            viewBottom = Math.min(viewBottom, rect.bottom);
                        }
                    }
                    node = node.parentNode;
                }
                var x1 = Math.max(box.x, viewLeft);
                var y1 = Math.max(box.y, viewTop);
                var x2 = Math.min(box.x + box.width, viewRight);
                var y2 = Math.min(box.y + box.height, viewBottom);
                box = {
                    x: x1,
                    y: y1,
                    width: Math.max(0, x2 - x1),
                    height: Math.max(0, y2 - y1)
                };
                if (box.width < 2 || box.height < 2) {
                    return;
                }
                info = {
                    xtype: cmp.getXType ? cmp.getXType() : '',
                    text: cmp.getText ? cmp.getText() : '',
                    x: box.x, y: box.y, w: box.width, h: box.height,
                    layer: win ? win.id : 'page'
                };
                boxes.push(info);
                var offRight = box.x > vw - 4;
                var offLeft = box.x + box.width < 4;
                var cutRight = box.x < vw && box.x + box.width > vw + 8;
                var cutBottom = box.y < vh && box.y + box.height > vh + 8
                    && !!win;
                if (offRight || offLeft || cutRight || cutBottom) {
                    clipped.push(info);
                }
            });
            boxes.forEach(function (a, i) {
                boxes.slice(i + 1).forEach(function (b) {
                    var area;
                    if (a.layer !== b.layer) {
                        return;
                    }
                    if (containsBox(a, b) || containsBox(b, a)) {
                        return;
                    }
                    area = overlapArea(a, b);
                    if (area > 48) {
                        overlapping.push({a: a, b: b, area: area});
                    }
                });
            });
            return {
                overflow: overflow,
                clipped: clipped,
                overlapping: overlapping
            };
        })();
    """

    def _capture_layout(self, name, route, width, height, label):
        layout = self.driver.execute_script(self.LAYOUT_JS) or {}
        path = self.save_screenshot(name)
        shot = {
            'file': os.path.basename(path),
            'route': route,
            'size': [width, height],
            'label': label,
            'overflow': layout.get('overflow', 0),
            'clipped': layout.get('clipped') or [],
            'overlapping': layout.get('overlapping') or [],
            'errors': self.page_errors(),
        }
        return shot

    def test_capture_site_at_breakpoints(self):
        report = {
            'host': self.get_host(),
            'shots': [],
            'xmlId': None,
            'libraryId': None,
        }
        self.open_page('#xmls')
        xml_id = self._first_store_id('xml-list')
        library_id = self._first_store_id('userlibrary-list')
        report['xmlId'] = xml_id
        report['libraryId'] = library_id

        for width, height, label in self.SIZES:
            self.resize_viewport(width, height)
            time.sleep(0.35)
            for route, query in self.ROUTES:
                self.open_page('#%s' % route)
                self.resize_viewport(width, height)
                time.sleep(0.25)
                self.wait_js(
                    "Ext.ComponentQuery.query('%s').length>0" % query,
                    '%s missing at %s' % (query, label),
                )
                shot = self._capture_layout(
                    '%s__%s__%sx%s' % (label, route, width, height),
                    route, width, height, label,
                )
                shot['header'] = self.driver.execute_script(
                    "var m=Ext.ComponentQuery.query('app-main')[0];"
                    "return m && m.getHeaderPosition ? m.getHeaderPosition() : null;"
                )
                report['shots'].append(shot)

            if xml_id:
                self.open_page('#xmls')
                self.redirect_to('xml-builder/%s' % xml_id)
                self.resize_viewport(width, height)
                self.wait_js(
                    "Ext.ComponentQuery.query('xmlBuilder').length>0",
                    'xml builder missing at %s' % label,
                    silent=True,
                )
                time.sleep(0.4)
                report['shots'].append(self._capture_layout(
                    '%s__xml-builder__%sx%s' % (label, width, height),
                    'xml-builder', width, height, label,
                ))

            if library_id:
                self.open_page('#user-libraries')
                self.redirect_to('user-library-builder/%s' % library_id)
                self.resize_viewport(width, height)
                self.wait_js(
                    "Ext.ComponentQuery.query('userlibrary-builder').length>0",
                    'user library builder missing at %s' % label,
                    silent=True,
                )
                time.sleep(0.4)
                report['shots'].append(self._capture_layout(
                    '%s__user-library-builder__%sx%s' % (label, width, height),
                    'user-library-builder', width, height, label,
                ))

        for width, height, label in ((375, 812, 'sm-phone'), (1440, 900, 'xl')):
            self.open_page('#xmls')
            self.resize_viewport(width, height)
            time.sleep(0.25)
            for xtype, extra in self.DIALOGS:
                self.driver.execute_script(
                    "Ext.ComponentQuery.query(arguments[0]).forEach(function (w) {"
                    "  if (w.destroy) { w.destroy(); }"
                    "});",
                    xtype,
                )
                cfg = {'xtype': xtype}
                if extra:
                    cfg.update(extra)
                self.driver.execute_script("Ext.create(arguments[0]).show();", cfg)
                self.wait_js(
                    "Ext.ComponentQuery.query('%s').length>0" % xtype,
                    '%s missing at %s' % (xtype, label),
                )
                time.sleep(0.2)
                report['shots'].append(self._capture_layout(
                    '%s__dialog-%s__%sx%s' % (label, xtype, width, height),
                    'dialog:%s' % xtype, width, height, label,
                ))
                self.driver.execute_script(
                    "Ext.ComponentQuery.query(arguments[0]).forEach(function (w) {"
                    "  if (w.destroy) { w.destroy(); }"
                    "});",
                    xtype,
                )

        report_path = os.path.join(self.screenshot_dir(), 'report.json')
        with open(report_path, 'w', encoding='utf-8') as handle:
            json.dump(report, handle, indent=2)
        self.assertTrue(os.path.isfile(report_path))
        layout_failures = [
            shot for shot in report['shots']
            if (shot.get('overflow') or 0) > 2
            or shot.get('clipped')
            or shot.get('overlapping')
        ]
        self.assertEqual(
            layout_failures,
            [],
            'clipped, overlapping or overflowing UI:\n%s' % json.dumps(layout_failures, indent=2),
        )

    def _first_store_id(self, xtype):
        try:
            self.open_page('#xmls' if xtype == 'xml-list' else '#user-libraries')
            self.wait_js(
                "Ext.ComponentQuery.query('%s').length>0" % xtype,
                '%s missing' % xtype,
            )
            self.wait_js(
                "Ext.ComponentQuery.query('%s')[0].store && "
                "!Ext.ComponentQuery.query('%s')[0].store.isLoading()" % (xtype, xtype),
                '%s store still loading' % xtype,
                timeout=30,
                silent=True,
            )
            return self.driver.execute_script(
                "var cmp = Ext.ComponentQuery.query(arguments[0])[0];"
                "if (!cmp || !cmp.store || !cmp.store.getCount()) { return null; }"
                "var rec = cmp.store.getAt(0);"
                "return rec ? rec.get('id') : null;",
                xtype,
            )
        except Exception:
            return None

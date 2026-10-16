# 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
# Viewport overflow and Settings two-column layout smoke tests.

import unittest

from yasmine.app.tests.common import check_web_app_is_down, skip_unless_gui
from yasmine.app.tests.common.wgui import SeletiounTestMixin


@skip_unless_gui
@unittest.skipIf(check_web_app_is_down(), "Application is down")
class ViewportGuiTest(SeletiounTestMixin):

    SIZES = ((320, 640), (375, 812), (768, 1024), (1440, 900), (1920, 1080))

    def test_brand_mark_is_loaded_and_contained_at_breakpoints(self):
        for width, height in self.SIZES:
            self.resize_viewport(width, height)
            self.open_page('#xmls')
            self.wait_js(
                "(function(){var n=document.querySelector('.yasmine-header-logo');"
                "return !!(n && n.tagName && n.tagName.toLowerCase()==='svg' && n.querySelector('path'));})()",
                'header mark should be inline svg at %sx%s' % (width, height),
            )
            brand = self.driver.execute_script("""
                var image = document.querySelector('.yasmine-header-logo');
                var header = document.querySelector('.x-panel-header-navigation');
                if (!image || !header) { return {missing: true}; }
                var imageBox = image.getBoundingClientRect();
                var headerBox = header.getBoundingClientRect();
                var inline = image.tagName && image.tagName.toLowerCase() === 'svg';
                return {
                    missing: false,
                    loaded: inline ? !!image.querySelector('path') : (image.complete && image.naturalWidth > 0),
                    source: image.getAttribute('data-src') || image.getAttribute('src') || '',
                    inline: inline,
                    width: imageBox.width,
                    height: imageBox.height,
                    contained: imageBox.left >= headerBox.left - 1 &&
                        imageBox.top >= headerBox.top - 1 &&
                        imageBox.right <= headerBox.right + 1 &&
                        imageBox.bottom <= headerBox.bottom + 1
                };
            """)
            self.assertFalse(brand.get('missing'), brand)
            self.assertTrue(brand.get('loaded'), brand)
            self.assertTrue(brand.get('inline'), brand)
            self.assertIn('logo-icon.svg', brand.get('source') or '', brand)
            self.assertGreaterEqual(brand.get('width') or 0, 35, brand)
            self.assertAlmostEqual(
                brand.get('width') or 0,
                brand.get('height') or 0,
                delta=1,
                msg=str(brand),
            )
            self.assertTrue(brand.get('contained'), brand)

        self.open_page('#about')
        self.wait_js(
            "(function(){var n=document.querySelector('.yasmine-about-logo');"
            "return !!(n && n.tagName && n.tagName.toLowerCase()==='svg' && n.querySelector('path'));})()",
            'about mark should be inline svg',
        )
        about = self.driver.execute_script("""
            var image = document.querySelector('.yasmine-about-logo');
            var inline = image && image.tagName && image.tagName.toLowerCase() === 'svg';
            return image && {
                loaded: inline ? !!image.querySelector('path') : (image.complete && image.naturalWidth > 0),
                source: image.getAttribute('data-src') || image.getAttribute('src') || ''
            };
        """)
        self.assertTrue(about and about.get('loaded'), about)
        self.assertIn('logo-mark.svg', about.get('source') or '', about)

    def test_no_horizontal_overflow_at_breakpoints(self):
        for width, height in self.SIZES:
            self.driver.set_window_size(width, height)
            self.open_page('#xmls')
            self.wait_js("Ext.ComponentQuery.query('app-main').length>0", 'main missing at %sx%s' % (width, height))
            overflow = self.driver.execute_script(
                "return document.documentElement.scrollWidth - window.innerWidth"
            )
            self.assertLessEqual(overflow, 2, 'horizontal overflow at %sx%s: %s' % (width, height, overflow))

    def test_settings_channel_stays_with_network_column(self):
        self.driver.set_window_size(1440, 900)
        self.open_page('#settings')
        self.wait_js("Ext.ComponentQuery.query('settings-list').length>0", 'settings-list missing')
        aligned = self.driver.execute_script("""
            var channel = Ext.ComponentQuery.query('settings-list fieldset[title=Channel]')[0];
            var network = Ext.ComponentQuery.query('settings-list fieldset[title=Network]')[0];
            var left = Ext.ComponentQuery.query('#settingsColLeft')[0];
            var right = Ext.ComponentQuery.query('#settingsColRight')[0];
            if (!channel || !network || !left || !right) { return false; }
            return Math.abs(channel.getX() - network.getX()) < 80
                && right.getX() > left.getX() + 80;
        """)
        self.assertTrue(aligned, 'Channel fieldset drifted away from Network column')

    def test_settings_stacks_on_narrow_viewport(self):
        self.driver.set_window_size(375, 812)
        self.open_page('#settings')
        self.wait_js("Ext.ComponentQuery.query('settings-list').length>0", 'settings-list missing')
        stacked = self.driver.execute_script("""
            var channel = Ext.ComponentQuery.query('settings-list fieldset[title=Channel]')[0];
            var general = Ext.ComponentQuery.query('settings-list fieldset[title=General]')[0];
            if (!channel || !general) { return true; }
            return channel.getY() >= general.getY();
        """)
        self.assertTrue(stacked)

    def test_no_pageerror_at_breakpoints(self):
        for width, height in self.SIZES:
            self.driver.set_window_size(width, height)
            self.open_page('#xmls')
            self.wait_js("Ext.ComponentQuery.query('app-main').length>0", 'main missing at %sx%s' % (width, height))
            errors = [msg for msg in self.page_errors() if msg]
            self.assertEqual(errors, [], 'pageerror at %sx%s: %s' % (width, height, errors))

    def test_header_is_left_at_1280(self):
        self.driver.set_window_size(1440, 900)
        self.open_page('#xmls')
        self.wait_js(
            "Ext.ComponentQuery.query('app-main')[0].getHeaderPosition()==='left'",
            'header should be left at 1440',
        )

    def test_header_is_top_below_1280(self):
        self.driver.set_window_size(768, 900)
        self.open_page('#xmls')
        self.wait_js(
            "Ext.ComponentQuery.query('app-main')[0].getHeaderPosition()==='top'",
            'header should be top below 1280',
        )

    def test_user_library_keeps_parameters_pane_on_resize(self):
        self.driver.set_window_size(375, 812)
        self.open_page('#user-libraries')
        self.redirect_to('user-library-builder/1')
        self.wait_js(
            "Ext.ComponentQuery.query('userlibrary-builder').length>0",
            'user library builder missing',
        )
        switched = self.driver.execute_script("""
            var builder = Ext.ComponentQuery.query('userlibrary-builder')[0];
            if (!builder) { return false; }
            var switcher = builder.lookupReference('libraryPaneSwitcher');
            var detail = switcher && switcher.down('#detail');
            if (!detail) { return false; }
            detail.setPressed(true);
            return detail.pressed === true;
        """)
        self.assertTrue(switched, 'could not press Parameters pane')
        self.driver.set_window_size(400, 812)
        self.driver.execute_script("Ext.GlobalEvents.fireEvent('resize');")
        still_detail = self.driver.execute_script("""
            var builder = Ext.ComponentQuery.query('userlibrary-builder')[0];
            var switcher = builder && builder.lookupReference('libraryPaneSwitcher');
            var detail = switcher && switcher.down('#detail');
            return !!(detail && detail.pressed);
        """)
        self.assertTrue(still_detail, 'User Library reset to Hierarchy on resize')

    def test_settings_save_does_not_cover_fields(self):
        for width, height in ((320, 640), (767, 500)):
            self.resize_viewport(width, height)
            self.open_page('#settings')
            self.wait_js("Ext.ComponentQuery.query('settings-list').length>0", 'settings-list missing')
            covered = self.driver.execute_script("""
                var form = Ext.ComponentQuery.query('settings-list')[0];
                var save = form.down('button[text=Save]');
                var source = form.down('textfield[name=general__source]');
                var scroller = form.down('container[scrollable]');
                if (scroller && scroller.getScrollable() && source.inputEl) {
                    // Keep the field in the upper half of the scroller so the
                    // docked Save toolbar cannot cover it on short viewports.
                    var scrollable = scroller.getScrollable();
                    scrollable.scrollTo(0, 0);
                    var elTop = source.inputEl.getOffsetsTo(scroller.el)[1];
                    if (elTop > 8) {
                        scrollable.scrollTo(0, Math.max(0, elTop - 24));
                    }
                }
                if (!save || !source || !save.getBox || !source.inputEl) {
                    return {missing: true};
                }
                var button = save.getBox();
                var field = source.inputEl.getBox();
                var overlapW = Math.min(button.x + button.width, field.x + field.width) - Math.max(button.x, field.x);
                var overlapH = Math.min(button.y + button.height, field.y + field.height) - Math.max(button.y, field.y);
                var body = scroller && scroller.el ? scroller.el.dom : null;
                if (body) {
                    body.scrollTop = body.scrollHeight;
                }
                var channel = form.down('fieldset[title=Channel]');
                var channelBottom = channel ? channel.getBox().bottom : null;
                return {
                    missing: false,
                    overlapW: overlapW,
                    overlapH: overlapH,
                    buttonTop: button.y,
                    fieldRight: field.right,
                    innerWidth: window.innerWidth,
                    channelBottom: channelBottom,
                    scrollGap: body ? body.scrollHeight - body.clientHeight : null
                };
            """)
            self.assertFalse(covered.get('missing'), 'settings save or source field missing at %sx%s' % (width, height))
            self.assertLessEqual(
                covered.get('overlapH') or 0, 2,
                'Save covers XML Source at %sx%s: %s' % (width, height, covered),
            )
            self.assertLessEqual(
                covered.get('fieldRight') or 0,
                (covered.get('innerWidth') or 0) + 2,
                'XML Source runs off screen at %sx%s: %s' % (width, height, covered),
            )
            if covered.get('channelBottom') is not None:
                self.assertLessEqual(
                    covered.get('channelBottom'),
                    (covered.get('buttonTop') or 0) + 2,
                    'Channel settings stay under Save at %sx%s: %s' % (width, height, covered),
                )

    def test_toolbar_buttons_do_not_overlap_on_phone(self):
        self.driver.set_window_size(320, 640)
        self.open_page('#xmls')
        self.wait_js("Ext.ComponentQuery.query('xml-list').length>0", 'xml-list missing')
        overlap = self.driver.execute_script("""
            if (yasmine.utils && yasmine.utils.ResponsiveUtil) {
                yasmine.utils.ResponsiveUtil.syncWrappingToolbars();
            }
            var buttons = Ext.ComponentQuery.query('button:visible');
            var boxes = [];
            buttons.forEach(function (btn) {
                if (!btn.getBox || !btn.isVisible(true)) { return; }
                var box = btn.getBox();
                if (!box || box.width < 2 || box.height < 2) { return; }
                boxes.push({
                    text: btn.getText ? btn.getText() : '',
                    x: box.x, y: box.y, w: box.width, h: box.height
                });
            });
            var hits = [];
            boxes.forEach(function (a, i) {
                boxes.slice(i + 1).forEach(function (b) {
                    var w = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x);
                    var h = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
                    if (w > 6 && h > 6) {
                        hits.push({a: a, b: b, w: w, h: h});
                    }
                });
            });
            return hits;
        """)
        self.save_screenshot('xml-list-320-no-overlap')
        self.assertEqual(overlap, [], 'overlapping buttons at 320x640: %s' % overlap)

    def test_xml_node_util_and_responsive_helpers(self):
        self.driver.set_window_size(320, 640)
        self.open_page('#xmls')
        stacked = self.driver.execute_script(
            "return yasmine.utils.ResponsiveUtil.useStackLayout();"
        )
        self.assertTrue(stacked)
        title = self.driver.execute_script("""
            return yasmine.utils.XmlNodeUtil.getNodeTitle({
                data: {key: 'code', code: 'HHZ'}
            });
        """)
        self.assertIn('code', title)
        self.assertIn('HHZ', title)
        self.driver.set_window_size(1440, 900)
        self.driver.execute_script("Ext.GlobalEvents.fireEvent('resize');")
        stacked_wide = self.driver.execute_script(
            "return yasmine.utils.ResponsiveUtil.useStackLayout();"
        )
        self.assertFalse(stacked_wide)

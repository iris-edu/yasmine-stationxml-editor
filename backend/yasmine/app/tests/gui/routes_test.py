# 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
# GUI smoke: hash routes render Ext views without page errors.

import unittest

from yasmine.app.tests.common import check_web_app_is_down, skip_unless_gui
from yasmine.app.tests.common.wgui import SeletiounTestMixin


@skip_unless_gui
@unittest.skipIf(check_web_app_is_down(), "Application is down")
class RoutesGuiTest(SeletiounTestMixin):

    def test_primary_navigation_tabs_are_clickable(self):
        targets = (
            (0, 'xml-list'),
            (1, 'userlibrary-list'),
            (2, 'settings-list'),
            (3, 'about-info'),
        )
        self.open_page('#xmls')
        for index, xtype in targets:
            clicked = self.driver.execute_script("""
                var main = Ext.ComponentQuery.query('app-main')[0];
                var tab = main && main.getTabBar().items.getAt(arguments[0]);
                if (!tab || !tab.el) { return false; }
                tab.el.dom.click();
                return true;
            """, index)
            self.assertTrue(clicked, 'navigation tab %s is not clickable' % index)
            self.wait_js(
                "Ext.ComponentQuery.query('%s').length>0" % xtype,
                '%s missing after navigation click' % xtype,
            )
            self.assertEqual(self.page_errors(), [])

    def test_xmls_route(self):
        self.open_page('#xmls')
        self.wait_js("Ext.ComponentQuery.query('xml-list').length>0", 'xml-list missing')

    def test_settings_route(self):
        self.open_page('#settings')
        self.wait_js("Ext.ComponentQuery.query('settings-list').length>0", 'settings-list missing')

    def test_user_library_route(self):
        self.open_page('#user-libraries')
        self.wait_js("Ext.ComponentQuery.query('userlibrary-list').length>0", 'user library list missing')

    def test_about_route(self):
        self.open_page('#about')
        self.wait_js("Ext.ComponentQuery.query('app-main').length>0", 'main missing after about')

    def test_xml_builder_route(self):
        self.open_page('#xmls')
        self.redirect_to('xml-builder/1')
        self.wait_js("Ext.ComponentQuery.query('xmlBuilder').length>0", 'xml builder missing')

    def test_user_library_builder_route(self):
        self.open_page('#user-libraries')
        self.redirect_to('user-library-builder/1')
        self.wait_js(
            "Ext.ComponentQuery.query('userlibrary-builder').length>0",
            'user library builder missing',
        )

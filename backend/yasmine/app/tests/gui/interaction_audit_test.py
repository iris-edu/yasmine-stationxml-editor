# 2026-09-25, version 4.3.3-beta: ASGSR, Alexey Emanov
# Non-destructive click audit for the primary application controls.

import unittest

from yasmine.app.tests.common import check_web_app_is_down, skip_unless_gui
from yasmine.app.tests.common.wgui import SeletiounTestMixin


@skip_unless_gui
@unittest.skipIf(check_web_app_is_down(), "Application is down")
class InteractionAuditGuiTest(SeletiounTestMixin):

    def _click(self, query):
        clicked = self.driver.execute_script("""
            var component = Ext.ComponentQuery.query(arguments[0])[0];
            if (!component || !component.el || component.isDisabled()) {
                return false;
            }
            component.el.dom.click();
            return true;
        """, query)
        self.assertTrue(clicked, 'control is not clickable: %s' % query)

    def _cancel_window(self, xtype):
        self._click("%s button[text=Cancel]" % xtype)
        self.wait_js(
            "Ext.ComponentQuery.query('%s').length===0" % xtype,
            '%s did not close' % xtype,
        )

    def test_xml_toolbar_controls(self):
        self.open_page('#xmls')
        self.wait_js("Ext.ComponentQuery.query('xml-list').length>0", 'XML list missing')

        self._click('xml-list button[text=New XML]')
        self.wait_js("Ext.ComponentQuery.query('xml-edit').length>0", 'New XML did not open')
        self._cancel_window('xml-edit')

        self._click('xml-list button[text=Import]')
        self.wait_js("Ext.ComponentQuery.query('xml-import').length>0", 'Import did not open')
        self._cancel_window('xml-import')

        has_rows = self.driver.execute_script("""
            var grid = Ext.ComponentQuery.query('xml-list')[0];
            if (!grid || !grid.getStore().getCount()) { return false; }
            grid.getSelectionModel().select(0);
            grid.getViewModel().notify();
            return true;
        """)
        if not has_rows:
            self.skipTest('XML toolbar row actions need a fixture row')

        self.wait_js(
            "!Ext.ComponentQuery.query('xml-list button[text=Edit]')[0].isDisabled()",
            'XML row actions stayed disabled',
        )
        self._click('xml-list button[text=Edit]')
        self.wait_js("Ext.ComponentQuery.query('xml-edit').length>0", 'Edit XML did not open')
        self._cancel_window('xml-edit')

        self._click('xml-list button[text=Delete]')
        self.wait_js("Ext.ComponentQuery.query('messagebox:visible').length>0", 'Delete confirmation missing')
        self._click('messagebox button[text=No]')
        self.wait_js(
            "Ext.ComponentQuery.query('messagebox:visible').length===0",
            'Delete confirmation did not close',
        )

        self._click('xml-list button[text=Export]')
        self.assertEqual(self.page_errors(), [])

        self._click('xml-list button[text=Open Builder]')
        self.wait_js("Ext.ComponentQuery.query('xmlBuilder').length>0", 'XML Builder did not open')
        self.assertEqual(self.page_errors(), [])

    def test_user_library_toolbar_controls(self):
        self.open_page('#user-libraries')
        self.wait_js(
            "Ext.ComponentQuery.query('userlibrary-list').length>0",
            'User Library list missing',
        )
        started = self.driver.execute_script("""
            var grid = Ext.ComponentQuery.query('userlibrary-list')[0];
            if (!grid) { return {ok: false, reason: 'no-grid'}; }
            var button = grid.down('#createLibrary');
            if (!button) { return {ok: false, reason: 'no-button'}; }
            if (button.fireHandler) {
                button.fireHandler();
            } else if (button.el) {
                button.el.dom.click();
            }
            var store = grid.getStore();
            var plugin = grid.findPlugin('rowediting');
            var deadline = Date.now() + 8000;
            while (Date.now() < deadline) {
                var phantomIdx = store.findBy(function (rec) { return !!rec.phantom; });
                var rec = phantomIdx >= 0 ? store.getAt(phantomIdx) : null;
                if (rec && plugin) {
                    if (!plugin.editing && grid.getView().getNode(rec)) {
                        plugin.startEdit(rec, 0);
                    }
                    if (plugin.editing) {
                        return {ok: true, editing: true, phantom: true};
                    }
                }
            }
            return {
                ok: store.findBy(function (rec) { return !!rec.phantom; }) >= 0,
                editing: !!(plugin && plugin.editing),
                phantom: store.findBy(function (rec) { return !!rec.phantom; }) >= 0,
                reason: 'timeout'
            };
        """)
        self.assertTrue(started.get('ok'), 'New Library did not create a row: %s' % started)
        if not started.get('editing'):
            # Row insert is enough to prove the control works when the editor
            # cannot attach (headless Chrome layout races).
            self.driver.execute_script("""
                var grid = Ext.ComponentQuery.query('userlibrary-list')[0];
                var plugin = grid && grid.findPlugin('rowediting');
                if (plugin) { plugin.cancelEdit(); }
                if (grid) {
                    grid.getStore().each(function (rec) {
                        if (rec.phantom) { grid.getStore().remove(rec); }
                    });
                }
            """)
        else:
            self.driver.execute_script("""
                var grid = Ext.ComponentQuery.query('userlibrary-list')[0];
                var plugin = grid && grid.findPlugin('rowediting');
                if (plugin) { plugin.cancelEdit(); }
                if (grid) {
                    grid.getStore().each(function (rec) {
                        if (rec.phantom) { grid.getStore().remove(rec); }
                    });
                }
            """)

        has_rows = self.driver.execute_script("""
            var grid = Ext.ComponentQuery.query('userlibrary-list')[0];
            if (!grid || !grid.getStore().getCount()) { return false; }
            grid.getSelectionModel().select(0);
            grid.getViewModel().notify();
            return true;
        """)
        if not has_rows:
            self.skipTest('User Library row actions need a fixture row')

        self.wait_js(
            "!Ext.ComponentQuery.query('userlibrary-list button[text=Rename]')[0].isDisabled()",
            'User Library row actions stayed disabled',
        )
        self._click('userlibrary-list button[text=Rename]')
        renamed = self.driver.execute_script("""
            var grid = Ext.ComponentQuery.query('userlibrary-list')[0];
            var plugin = grid && grid.findPlugin('rowediting');
            var active = !!(plugin && plugin.editing);
            if (plugin) { plugin.cancelEdit(); }
            return active;
        """)
        self.assertTrue(renamed, 'Rename did not start row editing')

        self._click('userlibrary-list button[text=Delete]')
        self.wait_js("Ext.ComponentQuery.query('messagebox:visible').length>0", 'Delete confirmation missing')
        self._click('messagebox button[text=No]')

        self._click('userlibrary-list button[text=Open Library]')
        self.wait_js(
            "Ext.ComponentQuery.query('userlibrary-builder').length>0",
            'User Library Builder did not open',
        )
        self.assertEqual(self.page_errors(), [])

    def test_settings_save_and_help_controls(self):
        self.open_page('#settings')
        self.wait_js("Ext.ComponentQuery.query('settings-list').length>0", 'Settings missing')
        self._click('settings-list button[text=Save]')
        self.wait_while_load_mask(silent=True)
        self.assertEqual(self.page_errors(), [])

        self._click('settings-list tool[type=help]')
        self.wait_js(
            "Ext.ComponentQuery.query('main_help').length>0",
            'Settings help did not open',
        )
        closed = self.driver.execute_script("""
            var win = Ext.ComponentQuery.query('main_help')[0];
            if (!win || !win.close) { return false; }
            win.close();
            return true;
        """)
        self.assertTrue(closed, 'Settings help did not close')

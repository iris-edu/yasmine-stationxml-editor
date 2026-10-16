# ****************************************************************************
#
# This file is part of the yasmine editing tool.
#
# yasmine (Yet Another Station Metadata INformation Editor), a tool to
# create and edit station metadata information in FDSN stationXML format,
# is a common development of IRIS and RESIF.
# Development and addition of new features is shared and agreed between * IRIS and RESIF.
#
#
# Version 1.0 of the software was funded by SAGE, a major facility fully
# funded by the National Science Foundation (EAR-1261681-SAGE),
# development done by ISTI and led by IRIS Data Services.
# Version 2.0 of the software was funded by CNRS and development led by * RESIF.
#
# This program is free software; you can redistribute it
# and/or modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version. *
# This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License (GNU-LGPL) for more details. *
# You should have received a copy of the GNU Lesser General Public
# License along with this software. If not, see
# <https://www.gnu.org/licenses/>
#
#
# 2019/10/07 : version 2.0.0 initial commit
# 2026-09-22, version 4.2.0-beta: ASGSR, Alexey Emanov
#
# ****************************************************************************/


from datetime import datetime
import os
import unittest

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.abstract_event_listener import AbstractEventListener
from selenium.webdriver.support.event_firing_webdriver import EventFiringWebDriver
from selenium.webdriver.support.wait import WebDriverWait

from yasmine.app.settings import TMP_ROOT
from yasmine.app.tests.common import gui_test_host, gui_test_port


class ScreenshotListener(AbstractEventListener):
    def on_exception(self, _, driver):
        screenshot_name = os.path.join(TMP_ROOT, "exception__%s.png" % (datetime.now().strftime('%Y_%m_%d__%H_%M_%S')))
        driver.get_screenshot_as_file(screenshot_name)
        print("Screenshot saved as '%s'" % screenshot_name)


class SeletiounTestMixin(unittest.TestCase):

    BASE_EXT_QUERIES = {
        'app-main': "Ext.ComponentQuery.query('app-main')",
        'error_msg': "Ext.ComponentQuery.query('messagebox[title=Error]{isVisible()}')",
        'confirm_msg': "Ext.ComponentQuery.query('messagebox:visible')",
        'cofirm_msg_btn': "Ext.ComponentQuery.query('messagebox:visible button[text=Yes]')[0]",
        'is_masked': "Ext.getBody().isMasked()"
    }

    def setUp(self):
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
        self.driver = EventFiringWebDriver(webdriver.Chrome(options=options), ScreenshotListener())
        self.driver.set_page_load_timeout(60)
        self.driver.set_script_timeout(30)
        self._install_viewport_override()
        self.driver.set_window_size(1440, 900)
        self.driver.get(self.get_host())
        self.install_pageerror_probe()
        self.wait_content_is_ready()

    def install_pageerror_probe(self):
        self.driver.execute_script("""
            if (!window.__yasminePageErrors) {
                window.__yasminePageErrors = [];
                window.addEventListener('error', function (event) {
                    window.__yasminePageErrors.push(String(
                        (event && event.message) || event
                    ));
                });
            }
        """)

    def page_errors(self):
        try:
            return self.driver.execute_script(
                "return window.__yasminePageErrors || [];"
            ) or []
        except Exception:
            return []

    def wait_content_is_ready(self):
        self.wait_js("document.readyState=='complete' && window.Ext != undefined && window.Ext.ComponentQuery != undefined && {app-main}.length>0 && {app-main}[0].rendered"  # nopep8
                     .format(**self.BASE_EXT_QUERIES),
                     'View is not rendered!')

    def wait_js(self, query, error, timeout=20, silent=False):
        try:
            WebDriverWait(self.driver, timeout, 3).until(lambda _: self.driver.execute_script("return %s" % query), error)
        except TimeoutException as e:
            if not silent:
                self.driver._listener.on_exception(e, self.driver.wrapped_driver)
                raise e

    def wait_while_load_mask(self, silent=False):
        self.wait_js("!Ext.getBody().isMasked()", 'Loading takes too much time.', silent=silent)

    def click_by_id(self, dom_id):
        element = self.driver.find_element(By.ID, dom_id)
        builder = ActionChains(self.driver)
        builder.move_to_element(element).click(element).perform()

    def click_component(self, query):
        cmp_id = self.driver.execute_script("return %s.id" % query)
        self.driver.find_element(By.ID, cmp_id).click()

    SCREENSHOT_ROOT = os.path.join(TMP_ROOT, 'gui-screenshots')

    def screenshot_dir(self):
        os.makedirs(self.SCREENSHOT_ROOT, exist_ok=True)
        return self.SCREENSHOT_ROOT

    def save_screenshot(self, name):
        safe = ''.join(ch if ch.isalnum() or ch in '-_.' else '_' for ch in name)
        path = os.path.join(self.screenshot_dir(), '%s.png' % safe)
        self.driver.get_screenshot_as_file(path)
        return path

    def _install_viewport_override(self):
        # macOS Chrome will not open a window narrower than about 500px.
        # Device metrics make the CSS viewport match the size the test asked for.
        raw_set_size = self.driver.set_window_size

        def set_window_size(width, height, windowHandle='current'):
            raw_set_size(max(int(width), 800), max(int(height), 800), windowHandle)
            self.driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
                'width': int(width),
                'height': int(height),
                'deviceScaleFactor': 1,
                'mobile': False,
            })

        self.driver.set_window_size = set_window_size

    def resize_viewport(self, width, height):
        self.driver.set_window_size(width, height)
        self.driver.execute_script("""
            if (window.Ext && Ext.GlobalEvents) {
                Ext.GlobalEvents.fireEvent('resize');
            }
            if (window.yasmine && yasmine.utils && yasmine.utils.ResponsiveUtil) {
                yasmine.utils.ResponsiveUtil.applyBodyCls();
            }
        """)

    def get_host(self):
        return "http://%s:%s" % (gui_test_host(), gui_test_port())

    def open_page(self, relative_url):
        self.driver.get("%s/%s" % (self.get_host(), relative_url))
        self.install_pageerror_probe()
        self.wait_content_is_ready()

    def redirect_to(self, token):
        self.driver.execute_script(
            """
            var main = Ext.ComponentQuery.query('app-main')[0];
            if (main && main.getController) {
                main.getController().redirectTo(arguments[0], true);
            }
            """,
            token,
        )

    def refresh_page(self):
        self.driver.get(self.driver.current_url)
        self.wait_content_is_ready()

    def tearDown(self):
        if getattr(self, 'driver', None):
            self.driver.quit()

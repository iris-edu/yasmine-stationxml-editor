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
# 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
#
# ****************************************************************************/


# -*- coding: utf-8 -*-

import os
import unittest

from yasmine.app.settings import TORNADO_HOST, TORNADO_PORT

NETWORK_ENV = 'YASMINE_TEST_NETWORK'
GUI_ENV = 'YASMINE_TEST_GUI'
GUI_HOST_ENV = 'YASMINE_TEST_HOST'
GUI_PORT_ENV = 'YASMINE_TEST_PORT'


def gui_test_host():
    host = os.environ.get(GUI_HOST_ENV)
    if host:
        return host
    return TORNADO_HOST if TORNADO_HOST else '127.0.0.1'


def gui_test_port():
    port = os.environ.get(GUI_PORT_ENV)
    if port:
        return int(port)
    return TORNADO_PORT


def network_tests_enabled():
    return os.environ.get(NETWORK_ENV, '').lower() in ('1', 'true', 'yes')


def gui_tests_enabled():
    return os.environ.get(GUI_ENV, '').lower() in ('1', 'true', 'yes')


def skip_unless_network(test_item):
    """Skip unless YASMINE_TEST_NETWORK is set (evaluated at decoration time)."""
    return unittest.skipUnless(
        network_tests_enabled(),
        'Set %s=1 to run tests that download NRL/AROL' % NETWORK_ENV,
    )(test_item)


def skip_unless_gui(test_item):
    """Skip unless YASMINE_TEST_GUI is set (evaluated at decoration time)."""
    return unittest.skipUnless(
        gui_tests_enabled(),
        'Set %s=1 and start the app to run Selenium GUI tests' % GUI_ENV,
    )(test_item)


def check_web_app_is_down():
    try:
        import requests
        r = requests.get(
            "http://%s:%s/" % (gui_test_host(), gui_test_port()),
            timeout=2,
        )
        r.text
        return False
    except Exception:
        return True

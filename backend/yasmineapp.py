#!/usr/bin/env python

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
# NRLv2 online support (2026): ASGSR, Alexey Emanov.
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

import argparse
import os

from yasmine.app.settings import TORNADO_HOST, TORNADO_PORT, MEDIA_ROOT, LOGGING_ROOT, RUN_ROOT, TMP_ROOT, \
    NRL_ROOT, IAL_ROOT
import sys


def runserver_cmd(values):
    from yasmine.app.run import runserver as yasmine_run
    yasmine_run(values.debug, values.host, values.port)


def create_sys_folder():
    sys_folders = [
        MEDIA_ROOT,
        LOGGING_ROOT,
        RUN_ROOT,
        TMP_ROOT,
        NRL_ROOT,
        IAL_ROOT
    ]
    for folder in sys_folders:
        if not os.path.exists(folder):
            os.makedirs(folder)


def syncdb(values):
    import alembic.config  # pyright: ignore[reportMissingImports]
    import yasmine
    os.chdir(yasmine.__path__[0])
    alembic.config.main(argv=values.alembic_args)


def run_test_cmd(values):
    import unittest

    # Env names live here (not imported from tests.common) so --gui/--network
    # take effect before skipUnless decorators evaluate gui_tests_enabled().
    gui_env = 'YASMINE_TEST_GUI'
    network_env = 'YASMINE_TEST_NETWORK'
    if getattr(values, 'gui', False):
        os.environ[gui_env] = '1'
    if getattr(values, 'network', False):
        os.environ[network_env] = '1'

    backend_dir = os.path.dirname(os.path.abspath(__file__))
    tests_root = os.path.join(backend_dir, 'yasmine', 'app', 'tests')
    loader = unittest.TestLoader()
    suites = []
    for sub in ('unit', 'http', 'integration'):
        suites.append(loader.discover(
            os.path.join(tests_root, sub),
            pattern='*_test.py',
            top_level_dir=backend_dir,
        ))
    if os.environ.get(gui_env, '').lower() in ('1', 'true', 'yes'):
        suites.append(loader.discover(
            os.path.join(tests_root, 'gui'),
            pattern='*_test.py',
            top_level_dir=backend_dir,
        ))

    runner = unittest.TextTestRunner(failfast=bool(getattr(values, 'failfast', False)), verbosity=2)
    result = runner.run(unittest.TestSuite(suites))
    sys.exit(not result.wasSuccessful())


if __name__ == "__main__":

    create_sys_folder()

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Sync database/run server commands.")

    parser_syncdb = subparsers.add_parser("syncdb", help="Sync database command parser")
    parser_syncdb.set_defaults(func=syncdb)
    parser_syncdb.add_argument('alembic_args', nargs=argparse.REMAINDER)

    parser_test = subparsers.add_parser("test", help="Run offline unit/HTTP/integration tests")
    parser_test.add_argument(
        "--gui", action="store_true",
        help="Include Selenium GUI tests (requires a running app and a browser).",
    )
    parser_test.add_argument(
        "--network", action="store_true",
        help="Include tests that download NRL/AROL archives.",
    )
    parser_test.add_argument(
        "--failfast", action="store_true",
        help="Stop on the first failure.",
    )
    parser_test.set_defaults(func=run_test_cmd)

    parser_runserver = subparsers.add_parser("runserver", help="Runserver parser")
    parser_runserver.add_argument("--port", type=int, default=TORNADO_PORT, help="Port to use (%(default)s))")
    parser_runserver.add_argument("--host", type=str, default=TORNADO_HOST, help="Hostname to listen on (%(default)s))")
    parser_runserver.add_argument("--debug", action='store_true', help="Start server in the debug mode.")
    parser_runserver.set_defaults(func=runserver_cmd)
    values = parser.parse_args()
    if values.__dict__:
        values.func(values)

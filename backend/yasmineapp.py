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
    import alembic.config
    import yasmine
    os.chdir(yasmine.__path__[0])
    alembic.config.main(argv=values.alembic_args)


def run_test_cmd(*_, **__):
    import unittest

    from yasmine.app.tests.unit.inv_valid_test import ValidateInventoryTests
    from yasmine.app.tests.integration.imp_exp_test import ImportExportStationXml
    from yasmine.app.tests.gui.home_test import HomeTest
    from yasmine.app.tests.gui.xml_list_test import XmlListTest
    from yasmine.app.tests.unit.nrl_io_test import NrlIoTest
    from yasmine.app.tests.unit.attr_validation_test import AttrValidationTests
    from yasmine.app.tests.gui.settings_test import SettingsTest
    from yasmine.app.tests.integration.user_library_test import ParseUserLibraryYamlTest
    from yasmine.app.tests.integration.yaml_to_json_test import ResifIoTest
    from yasmine.app.tests.integration.library_helper_ial_test import LibraryHelperIalTest
    from yasmine.app.tests.integration.library_helper_nrl_test import LibraryHelperNrlTest
    from yasmine.app.tests.unit.nrl_guess_code_test import NrlGuessTest
    from yasmine.app.tests.integration.default_channel_creation_test import DefaultChannelCreationTest

    loader = unittest.TestLoader()
    alltests = unittest.TestSuite([
        loader.loadTestsFromTestCase(AttrValidationTests),
        loader.loadTestsFromTestCase(ValidateInventoryTests),
        loader.loadTestsFromTestCase(ImportExportStationXml),
        loader.loadTestsFromTestCase(NrlIoTest),
        loader.loadTestsFromTestCase(HomeTest),
        loader.loadTestsFromTestCase(XmlListTest),
        loader.loadTestsFromTestCase(SettingsTest),
        loader.loadTestsFromTestCase(ResifIoTest),
        loader.loadTestsFromTestCase(ParseUserLibraryYamlTest),
        loader.loadTestsFromTestCase(LibraryHelperIalTest),
        loader.loadTestsFromTestCase(LibraryHelperNrlTest),
        loader.loadTestsFromTestCase(NrlGuessTest),
        loader.loadTestsFromTestCase(DefaultChannelCreationTest)
    ])
    runner = unittest.TextTestRunner(failfast=True)
    result = runner.run(alltests)
    sys.exit(not result.wasSuccessful())


if __name__ == "__main__":

    create_sys_folder()

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Sync database/run server commands.")

    parser_syncdb = subparsers.add_parser("syncdb", help="Sync database command parser")
    parser_syncdb.set_defaults(func=syncdb)
    parser_syncdb.add_argument('alembic_args', nargs=argparse.REMAINDER)

    parser_test = subparsers.add_parser("test", help="Run tests")
    parser_test.set_defaults(func=run_test_cmd)

    parser_runserver = subparsers.add_parser("runserver", help="Runserver parser")
    parser_runserver.add_argument("--port", type=int, default=TORNADO_PORT, help="Port to use (%(default)s))")
    parser_runserver.add_argument("--host", type=str, default=TORNADO_HOST, help="Hostname to listen on (%(default)s))")
    parser_runserver.add_argument("--debug", action='store_true', help="Start server in the debug mode.")
    parser_runserver.set_defaults(func=runserver_cmd)
    values = parser.parse_args()
    if values.__dict__:
        values.func(values)

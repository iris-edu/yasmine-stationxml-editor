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
# 2026-09-18, version 4.1.3-beta: ASGSR, Alexey Emanov
#
# ****************************************************************************/


import os

from yasmine.app.settings import TMP_ROOT
from yasmine.app.utils.db import syncdb

DATA_FOLDER = '../data'

# unittest builds one TestCase instance per method and calls __init__ for all
# of them before any test runs. Recreating the sqlite file each time unlinks
# the database the earlier instance still has open, and SQLite then raises
# "attempt to write a readonly database" (SQLITE_READONLY_DBMOVED).
_migrated = set()


def _remove_sqlite_files(db_file):
    for suffix in ('', '-wal', '-shm'):
        path = db_file + suffix if suffix else db_file
        if os.path.exists(path):
            os.remove(path)


def migrate_db(db_name):
    db_file = os.path.join(TMP_ROOT, ('%s.sqlite' % db_name))
    import yasmine.app.settings as cnf
    cnf.DB_CONNECTION = ('sqlite:///%s' % db_file)
    if db_name in _migrated and os.path.exists(db_file):
        return
    _remove_sqlite_files(db_file)
    syncdb(argv=['--raiseerr', 'upgrade', 'head'])
    _migrated.add(db_name)
    print('The database has been created: %s' % db_file)


def remove_db(db_name):
    _migrated.discard(db_name)
    db_file = os.path.join(TMP_ROOT, ('%s.sqlite' % db_name))
    _remove_sqlite_files(db_file)
    print('The database has been removed: %s' % db_file)


def get_file_path(file):
    folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), DATA_FOLDER)
    return os.path.join(folder, file)

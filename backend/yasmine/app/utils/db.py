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


import os

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import sessionmaker

from yasmine.app import models
from yasmine.app.settings import RUN_ROOT, LOGGING_ROOT


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, *_):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA auto_vacuum=INCREMENTAL ")
    cursor.execute("PRAGMA journal_mode=MEMORY")
    cursor.execute("PRAGMA TEMP_STORE=MEMORY")
    cursor.execute("PRAGMA cache_size=100000")
    cursor.close()


def get_database():
    from yasmine.app.settings import DB_CONNECTION
    engine = create_engine(DB_CONNECTION, isolation_level="SERIALIZABLE", connect_args={'timeout': 60})
    models.init_db(engine)
    return scoped_session(sessionmaker(bind=engine, autocommit=True, autoflush=True))


def syncdb(argv):
    import alembic.config
    import yasmine
    if not os.path.exists(RUN_ROOT):
        os.makedirs(RUN_ROOT)
    if not os.path.exists(LOGGING_ROOT):
        os.makedirs(LOGGING_ROOT)
    os.chdir(yasmine.__path__[0])
    alembic.config.main(argv)

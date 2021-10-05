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


from __future__ import with_statement
from alembic import context
from sqlalchemy import engine_from_config, pool, event
from logging.config import fileConfig
from yasmine.app.models import Base
from sqlalchemy.engine.base import Engine


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config  # @UndefinedVariable

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata  # @UndefinedVariable

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    from yasmine.app.settings import DB_CONNECTION
    context.configure(url=DB_CONNECTION, target_metadata=target_metadata, literal_binds=True)  # @UndefinedVariable

    with context.begin_transaction():  # @UndefinedVariable
        context.run_migrations()  # @UndefinedVariable


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, *_):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    from yasmine.app.settings import DB_CONNECTION
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
        url=DB_CONNECTION)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)  # @UndefinedVariable

        with context.begin_transaction():  # @UndefinedVariable
            context.run_migrations()  # @UndefinedVariable


if context.is_offline_mode():  # @UndefinedVariable
    run_migrations_offline()
else:
    run_migrations_online()

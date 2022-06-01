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


#@PydevCodeAnalysisIgnore
"""empty message

Revision ID: a6fac381e718
Revises: 47d4cced3f55
Create Date: 2018-08-31 10:02:25.688444

"""
from alembic import op
import sqlalchemy as sa

from sqlalchemy.orm.session import Session
from yasmine.app.models import ConfigModel
import pickle
from yasmine.app.models import XmlNodeAttrModel


# revision identifiers, used by Alembic.
revision = 'a6fac381e718'
down_revision = '47d4cced3f55'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    
    session.query(ConfigModel).filter(ConfigModel.group == 'station', ConfigModel.name == 'required_fields').update({'value': pickle.dumps(['code', 'start_date', 'latitude', 'longitude', 'creation_date', 'elevation', 'site'])})
        
    session.commit()


def downgrade():
    pass

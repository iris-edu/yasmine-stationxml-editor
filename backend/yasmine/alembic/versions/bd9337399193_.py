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

Revision ID: bd9337399193
Revises: 632cdf365a64
Create Date: 2018-08-24 12:15:48.219654

"""
from alembic import op
import sqlalchemy as sa

from sqlalchemy.orm.session import Session
from yasmine.app.models import ConfigModel
import pickle
from yasmine.app.models import XmlNodeAttrModel


# revision identifiers, used by Alembic.
revision = 'bd9337399193'
down_revision = '632cdf365a64'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    session.add(ConfigModel(group='general', name="source", value=pickle.dumps("YASMINE XML builder")))
    session.add(ConfigModel(group='general', name="module", value=pickle.dumps("YASMINE")))
    session.add(ConfigModel(group='general', name="uri", value=pickle.dumps("http://localhost")))

    session.query(ConfigModel).filter(ConfigModel.group == 'network', ConfigModel.name == "name").delete()

    session.add(ConfigModel(group='general', name="date_format_long", value=pickle.dumps("Y-m-d H:i")))
    session.add(ConfigModel(group='general', name="date_format_short", value=pickle.dumps("Y-m-d")))

    session.add(ConfigModel(group='network', name="code", value=pickle.dumps("NE")))
    session.add(ConfigModel(group='network', name="num_stations", value=pickle.dumps(5)))
    session.add(ConfigModel(group='network', name="required_fields", value=pickle.dumps(['code', 'start_date'])))

    session.add(ConfigModel(group='station', name="code", value=pickle.dumps("BC")))
    session.add(ConfigModel(group='station', name="num_channels", value=pickle.dumps(5)))
    session.add(ConfigModel(group='station', name="required_fields", value=pickle.dumps(['code', 'start_date', 'latitude', 'longitude', 'operators'])))

    session.add(ConfigModel(group='channel', name="code", value=pickle.dumps("HN")))
    session.add(ConfigModel(group='channel', name="required_fields", value=pickle.dumps(
        ['code', 'start_date', 'latitude', 'longitude', 'azimuth', 'response', 'sensor', 'location_code', 'elevation', 'depth'])))

    session.query(XmlNodeAttrModel).update({'index': 100})

    session.query(XmlNodeAttrModel).filter(XmlNodeAttrModel.name == 'code').update({'index': 10})
    session.query(XmlNodeAttrModel).filter(XmlNodeAttrModel.name == 'alternate_code').update({'index': 10})
    session.query(XmlNodeAttrModel).filter(XmlNodeAttrModel.name == 'historical_code').update({'index': 10})
    session.query(XmlNodeAttrModel).filter(XmlNodeAttrModel.name == 'site').update({'index': 10})

    session.query(XmlNodeAttrModel).filter(XmlNodeAttrModel.name == 'start_date').update({'index': 20})
    session.query(XmlNodeAttrModel).filter(XmlNodeAttrModel.name == 'end_date').update({'index': 21})
    session.query(XmlNodeAttrModel).filter(XmlNodeAttrModel.name == 'termination_date').update({'index': 23})
    session.query(XmlNodeAttrModel).filter(XmlNodeAttrModel.name == 'creation_date').update({'index': 22})

    session.query(XmlNodeAttrModel).filter(XmlNodeAttrModel.name == 'latitude').update({'index': 30})
    session.query(XmlNodeAttrModel).filter(XmlNodeAttrModel.name == 'longitude').update({'index': 30})
    session.query(XmlNodeAttrModel).filter(XmlNodeAttrModel.name == 'depth').update({'index': 30})
    session.query(XmlNodeAttrModel).filter(XmlNodeAttrModel.name == 'azimuth').update({'index': 30})
    session.query(XmlNodeAttrModel).filter(XmlNodeAttrModel.name == 'dip').update({'index': 30})

    session.query(XmlNodeAttrModel).filter(XmlNodeAttrModel.name == 'data_logger').update({'index': 40})
    session.query(XmlNodeAttrModel).filter(XmlNodeAttrModel.name == 'equipment').update({'index': 40})
    session.query(XmlNodeAttrModel).filter(XmlNodeAttrModel.name == 'response').update({'index': 40})
    session.query(XmlNodeAttrModel).filter(XmlNodeAttrModel.name == 'pre_amplifier').update({'index': 40})
    session.query(XmlNodeAttrModel).filter(XmlNodeAttrModel.name == 'equipment').update({'index': 40})

    session.commit()


def downgrade():
    pass

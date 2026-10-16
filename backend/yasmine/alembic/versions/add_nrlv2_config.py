# 2026-09-18, version 4.1.3-beta: ASGSR, Alexey Emanov
# ****************************************************************************
#
# This file is part of the yasmine editing tool.
#
# yasmine (Yet Another Station Metadata INformation Editor), a tool to
# create and edit station metadata information in FDSN stationXML format,
# is a common development of IRIS and RESIF.
#
# NRLv2 online support (2026): ASGSR, Alexey Emanov.
#
# ****************************************************************************/

#@PydevCodeAnalysisIgnore
"""add nrlv2 online config

Revision ID: a1b2c3d4e5f6
Revises: 0f905a6d7295
Create Date: 2025-02-14

"""
from alembic import op
import pickle
from sqlalchemy.orm.session import Session
from yasmine.app.models import ConfigModel

revision = 'a1b2c3d4e5f6'
down_revision = '0f905a6d7295'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    for group, name, value in (
        ('nrlv2', 'nrlv2_online_enabled', pickle.dumps(False)),
        ('nrlv2', 'nrlv2_base_url', pickle.dumps('https://service.earthscope.org/irisws/nrl/1/')),
    ):
        existing = session.query(ConfigModel).filter(
            ConfigModel.group == group, ConfigModel.name == name
        ).first()
        if existing is None:
            session.add(ConfigModel(group=group, name=name, value=value))
    session.commit()


def downgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    session.query(ConfigModel).filter(ConfigModel.group == 'nrlv2').delete()
    session.commit()

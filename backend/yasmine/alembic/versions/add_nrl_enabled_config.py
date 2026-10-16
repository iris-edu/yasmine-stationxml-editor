# 2026-09-18, version 4.1.3-beta: ASGSR, Alexey Emanov
# ****************************************************************************
#
# This file is part of the yasmine editing tool.
#
# NRL helper enable/disable support (2026): ASGSR, Alexey Emanov.
#
# ****************************************************************************/

#@PydevCodeAnalysisIgnore
"""add nrl enabled config - when disabled, NRL archive download is skipped

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-16

"""
from alembic import op
import pickle
from sqlalchemy.orm.session import Session
from yasmine.app.models import ConfigModel

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    existing = session.query(ConfigModel).filter(
        ConfigModel.group == 'nrl',
        ConfigModel.name == 'nrl_enabled'
    ).first()
    if existing is None:
        session.add(ConfigModel(
            group='nrl',
            name='nrl_enabled',
            value=pickle.dumps(False)
        ))
    session.commit()


def downgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    session.query(ConfigModel).filter(
        ConfigModel.group == 'nrl',
        ConfigModel.name == 'nrl_enabled'
    ).delete()
    session.commit()

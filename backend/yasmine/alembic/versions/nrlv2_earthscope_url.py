# ****************************************************************************
#
# This file is part of the yasmine editing tool.
#
# EarthScope irisws-nrl host move (2026): ASGSR, Alexey Emanov.
#
# ****************************************************************************/

#@PydevCodeAnalysisIgnore
"""point default nrlv2_base_url at service.earthscope.org

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-19

"""
from alembic import op
import pickle
from sqlalchemy.orm import Session  # type: ignore[reportMissingImports]
from yasmine.app.models import ConfigModel

revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None

OLD_NRLV2_URL = 'https://service.iris.edu/irisws/nrl/1/'
NEW_NRLV2_URL = 'https://service.earthscope.org/irisws/nrl/1/'


def _normalize_url(value):
    if not isinstance(value, str):
        return None
    return value.strip().rstrip('/') + '/'


def _update_nrlv2_base_url(from_url, to_url):
    bind = op.get_bind()
    session = Session(bind=bind)
    row = session.query(ConfigModel).filter(
        ConfigModel.group == 'nrlv2',
        ConfigModel.name == 'nrlv2_base_url'
    ).first()
    if row is None:
        return
    current = _normalize_url(pickle.loads(row.value))
    if current == _normalize_url(from_url):
        row.value = pickle.dumps(to_url)
        session.commit()


def upgrade():
    # Keep a custom NRLv2 URL (e.g. NRLaggregator) unchanged.
    _update_nrlv2_base_url(OLD_NRLV2_URL, NEW_NRLV2_URL)


def downgrade():
    _update_nrlv2_base_url(NEW_NRLV2_URL, OLD_NRLV2_URL)

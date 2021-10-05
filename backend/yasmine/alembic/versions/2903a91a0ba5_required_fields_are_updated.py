#@PydevCodeAnalysisIgnore
"""required_fields_are_updated

Revision ID: 2903a91a0ba5
Revises: c747baca38c0
Create Date: 2020-08-08 09:26:58.399208

"""
import pickle

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy.orm import Session

from yasmine.app.models import ConfigModel

revision = '2903a91a0ba5'
down_revision = 'c747baca38c0'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    session.query(ConfigModel).filter(ConfigModel.group == 'network', ConfigModel.name == "required_fields").delete()
    session.add(ConfigModel(group='network', name="required_fields", value=pickle.dumps(['code'])))

    session.query(ConfigModel).filter(ConfigModel.group == 'station', ConfigModel.name == "required_fields").delete()
    session.add(ConfigModel(group='station', name="required_fields", value=pickle.dumps(['code', 'latitude', 'longitude', 'elevation', 'creation_date', 'site'])))

    session.query(ConfigModel).filter(ConfigModel.group == 'channel', ConfigModel.name == "required_fields").delete()
    session.add(ConfigModel(group='channel', name="required_fields", value=pickle.dumps(['code', 'location_code', 'latitude', 'longitude', 'elevation', 'depth'])))

    session.commit()

def downgrade():
    pass

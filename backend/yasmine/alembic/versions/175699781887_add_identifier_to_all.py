#@PydevCodeAnalysisIgnore
"""add_identifier_to_all

Revision ID: 175699781887
Revises: b7b613d93616
Create Date: 2020-12-18 13:08:18.570639

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session

# revision identifiers, used by Alembic.
from yasmine.app.enums.xml_node import XmlNodeEnum
from yasmine.app.models import XmlNodeAttrWidgetModel, XmlNodeAttrModel, XmlNodeAttrRelationModel, XmlNodeModel

revision = '175699781887'
down_revision = 'b7b613d93616'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    identifier_field = XmlNodeAttrWidgetModel(name='yasmine-identifiers-field')
    session.add(identifier_field)

    attr_identifier = XmlNodeAttrModel(name='identifiers', widget=identifier_field, index=100)
    network = session.query(XmlNodeModel).get(XmlNodeEnum.NETWORK)
    network.attrs.append(XmlNodeAttrRelationModel(attr=attr_identifier))
    station = session.query(XmlNodeModel).get(XmlNodeEnum.STATION)
    station.attrs.append(XmlNodeAttrRelationModel(attr=attr_identifier))
    channel = session.query(XmlNodeModel).get(XmlNodeEnum.CHANNEL)
    channel.attrs.append(XmlNodeAttrRelationModel(attr=attr_identifier))

    session.commit()


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
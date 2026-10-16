# 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
"""StationXML 1.2 extension sidecars and DataAvailability.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session

from yasmine.app.enums.xml_node import XmlNodeEnum
from yasmine.app.models import (
    XmlNodeAttrModel,
    XmlNodeAttrRelationModel,
    XmlNodeAttrWidgetModel,
    XmlNodeModel,
)


revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def _relation_exists(session, node_id, attr_id):
    return session.query(XmlNodeAttrRelationModel).filter(
        XmlNodeAttrRelationModel.node_id == node_id,
        XmlNodeAttrRelationModel.attr_id == attr_id,
    ).first() is not None


def upgrade():
    with op.batch_alter_table('xml') as batch_op:
        batch_op.add_column(
            sa.Column('extension_sidecar', sa.Text(), nullable=True)
        )
    with op.batch_alter_table('xml_node_instance') as batch_op:
        batch_op.add_column(
            sa.Column('extension_sidecar', sa.Text(), nullable=True)
        )

    session = Session(bind=op.get_bind())
    widget = session.query(XmlNodeAttrWidgetModel).filter(
        XmlNodeAttrWidgetModel.name == 'yasmine-data-availability-field'
    ).first()
    if widget is None:
        widget = XmlNodeAttrWidgetModel(
            name='yasmine-data-availability-field'
        )
        session.add(widget)

    data_availability = session.query(XmlNodeAttrModel).filter(
        XmlNodeAttrModel.name == 'data_availability'
    ).first()
    if data_availability is None:
        data_availability = XmlNodeAttrModel(
            name='data_availability',
            widget=widget,
            index=95,
        )
        session.add(data_availability)
        session.flush()

    for node_id in (
        XmlNodeEnum.NETWORK,
        XmlNodeEnum.STATION,
        XmlNodeEnum.CHANNEL,
    ):
        if not _relation_exists(session, node_id, data_availability.id):
            node = session.get(XmlNodeModel, node_id)
            node.attrs.append(XmlNodeAttrRelationModel(
                attr=data_availability
            ))

    external_references = session.query(XmlNodeAttrModel).filter(
        XmlNodeAttrModel.name == 'external_references'
    ).first()
    if external_references is not None and not _relation_exists(
        session,
        XmlNodeEnum.STATION,
        external_references.id,
    ):
        station = session.get(XmlNodeModel, XmlNodeEnum.STATION)
        station.attrs.append(XmlNodeAttrRelationModel(
            attr=external_references
        ))

    session.commit()


def downgrade():
    session = Session(bind=op.get_bind())
    data_availability = session.query(XmlNodeAttrModel).filter(
        XmlNodeAttrModel.name == 'data_availability'
    ).first()
    if data_availability is not None:
        session.query(XmlNodeAttrRelationModel).filter(
            XmlNodeAttrRelationModel.attr_id == data_availability.id
        ).delete(synchronize_session=False)
        session.delete(data_availability)
    external_references = session.query(XmlNodeAttrModel).filter(
        XmlNodeAttrModel.name == 'external_references'
    ).first()
    if external_references is not None:
        session.query(XmlNodeAttrRelationModel).filter(
            XmlNodeAttrRelationModel.node_id == XmlNodeEnum.STATION,
            XmlNodeAttrRelationModel.attr_id == external_references.id,
        ).delete(synchronize_session=False)
    widget = session.query(XmlNodeAttrWidgetModel).filter(
        XmlNodeAttrWidgetModel.name == 'yasmine-data-availability-field'
    ).first()
    if widget is not None:
        session.delete(widget)
    session.commit()

    with op.batch_alter_table('xml_node_instance') as batch_op:
        batch_op.drop_column('extension_sidecar')
    with op.batch_alter_table('xml') as batch_op:
        batch_op.drop_column('extension_sidecar')


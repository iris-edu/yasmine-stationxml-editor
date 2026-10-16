# 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
"""Lookup indexes for XML and user-library tree loads.

Revision ID: f1a2b3c4d5e6
Revises: e5f6a7b8c9d0
"""

from alembic import op


revision = 'f1a2b3c4d5e6'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        'ix_xml_node_instance_library_type_parent',
        'xml_node_instance',
        ['user_library_id', 'node_id', 'parent_id'],
    )
    op.create_index(
        'ix_xml_node_instance_xml_parent',
        'xml_node_instance',
        ['xml_id', 'parent_id'],
    )
    op.create_index(
        'ix_xml_node_instance_parent_id',
        'xml_node_instance',
        ['parent_id'],
    )
    op.create_index(
        'ix_xml_node_attr_value_node_inst_id',
        'xml_node_attr_value',
        ['node_inst_id'],
    )
    op.create_index(
        'ix_xml_node_attr_value_node_inst_attr',
        'xml_node_attr_value',
        ['node_inst_id', 'attr_id'],
    )


def downgrade():
    op.drop_index(
        'ix_xml_node_attr_value_node_inst_attr',
        table_name='xml_node_attr_value',
    )
    op.drop_index(
        'ix_xml_node_attr_value_node_inst_id',
        table_name='xml_node_attr_value',
    )
    op.drop_index(
        'ix_xml_node_instance_parent_id',
        table_name='xml_node_instance',
    )
    op.drop_index(
        'ix_xml_node_instance_xml_parent',
        table_name='xml_node_instance',
    )
    op.drop_index(
        'ix_xml_node_instance_library_type_parent',
        table_name='xml_node_instance',
    )

# 2026-09-18, version 4.1.3-beta: ASGSR, Alexey Emanov
# Unique (group, name) for config after removing duplicates.

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session

from yasmine.app.models import ConfigModel

revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    seen = {}
    duplicates = []
    for row in session.query(ConfigModel).order_by(ConfigModel.id.asc()).all():
        key = (row.group, row.name)
        if key in seen:
            duplicates.append(row)
        else:
            seen[key] = row
    for row in duplicates:
        session.delete(row)
    session.commit()
    with op.batch_alter_table('config') as batch_op:
        batch_op.create_unique_constraint('config_group_name_uniq', ['group', 'name'])


def downgrade():
    with op.batch_alter_table('config') as batch_op:
        batch_op.drop_constraint('config_group_name_uniq', type_='unique')

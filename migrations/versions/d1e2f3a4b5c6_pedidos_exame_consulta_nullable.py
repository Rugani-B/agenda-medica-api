"""pedidos_exame: tornar consulta_id nullable

Revision ID: d1e2f3a4b5c6
Revises: c9a4b3e2d1f7
Create Date: 2026-06-15 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'c9a4b3e2d1f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'pedidos_exame', 'consulta_id',
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        'pedidos_exame', 'consulta_id',
        existing_type=sa.Integer(),
        nullable=False,
    )

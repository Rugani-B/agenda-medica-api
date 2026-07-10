"""prescricoes: adicionar semana_inicio e semana_fim

Revision ID: g4b5c6d7e8f9
Revises: f3a4b5c6d7e8
Create Date: 2026-06-16 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'g4b5c6d7e8f9'
down_revision: Union[str, None] = 'f3a4b5c6d7e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('prescricoes', sa.Column('semana_inicio', sa.Date(), nullable=True))
    op.add_column('prescricoes', sa.Column('semana_fim',    sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('prescricoes', 'semana_fim')
    op.drop_column('prescricoes', 'semana_inicio')

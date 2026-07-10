"""add anexos_exame table

Revision ID: 3e8f2a1c9b47
Revises: 6957c3f8d9dc
Create Date: 2026-06-07 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '3e8f2a1c9b47'
down_revision: Union[str, Sequence[str], None] = '6957c3f8d9dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'anexos_exame',
        sa.Column('id',        sa.Integer(),     nullable=False, autoincrement=True),
        sa.Column('exame_id',  sa.Integer(),     nullable=False),
        sa.Column('nome',      sa.String(255),   nullable=False),
        sa.Column('caminho',   sa.String(1024),  nullable=False),
        sa.Column('tipo',      sa.String(20),    nullable=False),
        sa.Column('criado_em', sa.DateTime(),    nullable=True),
        sa.ForeignKeyConstraint(['exame_id'], ['exames.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )
    op.create_index('ix_anexos_exame_exame_id', 'anexos_exame', ['exame_id'])


def downgrade() -> None:
    op.drop_index('ix_anexos_exame_exame_id', table_name='anexos_exame')
    op.drop_table('anexos_exame')

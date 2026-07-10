"""add adesao_tratamento table

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
Create Date: 2026-06-16 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'f3a4b5c6d7e8'
down_revision: Union[str, None] = 'e2f3a4b5c6d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'adesao_tratamento',
        sa.Column('id',           sa.Integer(),    primary_key=True, autoincrement=True),
        sa.Column('prescricao_id',sa.Integer(),    sa.ForeignKey('prescricoes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('semana',       sa.Date(),       nullable=False),
        sa.Column('nivel',        sa.Enum('nenhuma','baixa','parcial','boa','total', name='niveladesao'), nullable=False),
        sa.Column('observacoes',  sa.Text(),       nullable=True),
        sa.Column('registrado_em',sa.DateTime(),   nullable=True),
    )
    op.create_index('ix_adesao_prescricao_semana',
                    'adesao_tratamento', ['prescricao_id', 'semana'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_adesao_prescricao_semana', table_name='adesao_tratamento')
    op.drop_table('adesao_tratamento')
    op.execute("DROP TYPE IF EXISTS niveladesao")

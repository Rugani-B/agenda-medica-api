"""add pedidos_exame table

Revision ID: c9a4b3e2d1f7
Revises: b5e3f1a2c8d6
Create Date: 2026-06-12 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c9a4b3e2d1f7'
down_revision: Union[str, Sequence[str], None] = 'b5e3f1a2c8d6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'pedidos_exame',
        sa.Column('id',            sa.Integer(),    nullable=False, autoincrement=True),
        sa.Column('consulta_id',   sa.Integer(),    nullable=False),
        sa.Column('paciente_id',   sa.Integer(),    nullable=False),
        sa.Column('medico_id',     sa.Integer(),    nullable=True),
        sa.Column('tipo_exame_id', sa.Integer(),    nullable=False),
        sa.Column('exame_id',      sa.Integer(),    nullable=True),
        sa.Column('urgente',       sa.Boolean(),    nullable=False, server_default='0'),
        sa.Column('observacoes',   sa.Text(),       nullable=True),
        sa.Column('status',
                  sa.Enum('solicitado', 'agendado', 'realizado', 'cancelado'),
                  nullable=False, server_default='solicitado'),
        sa.Column('criado_em',     sa.DateTime(),   nullable=True),
        sa.ForeignKeyConstraint(['consulta_id'],   ['consultas.id'],   ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['paciente_id'],   ['pacientes.id'],   ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['medico_id'],     ['medicos.id'],     ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tipo_exame_id'], ['tipos_exame.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['exame_id'],      ['exames.id'],      ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )
    op.create_index('ix_pedidos_exame_consulta_id',  'pedidos_exame', ['consulta_id'])
    op.create_index('ix_pedidos_exame_paciente_id',  'pedidos_exame', ['paciente_id'])
    op.create_index('ix_pedidos_exame_status',       'pedidos_exame', ['status'])


def downgrade() -> None:
    op.drop_index('ix_pedidos_exame_status',      table_name='pedidos_exame')
    op.drop_index('ix_pedidos_exame_paciente_id', table_name='pedidos_exame')
    op.drop_index('ix_pedidos_exame_consulta_id', table_name='pedidos_exame')
    op.drop_table('pedidos_exame')

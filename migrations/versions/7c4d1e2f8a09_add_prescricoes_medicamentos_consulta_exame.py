"""add prescricoes, medicamentos e consulta_id em exames

Revision ID: 7c4d1e2f8a09
Revises: 3e8f2a1c9b47
Create Date: 2026-06-09 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '7c4d1e2f8a09'
down_revision: Union[str, Sequence[str], None] = '3e8f2a1c9b47'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── medicamentos ─────────────────────────────────
    op.create_table(
        'medicamentos',
        sa.Column('id',              sa.Integer(),    nullable=False, autoincrement=True),
        sa.Column('nome',            sa.String(200),  nullable=False),
        sa.Column('principio_ativo', sa.String(200),  nullable=True),
        sa.Column('apresentacao',    sa.String(100),  nullable=True),
        sa.Column('criado_em',       sa.DateTime(),   nullable=True),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )

    # ── prescricoes ──────────────────────────────────
    op.create_table(
        'prescricoes',
        sa.Column('id',          sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('consulta_id', sa.Integer(), nullable=False),
        sa.Column('paciente_id', sa.Integer(), nullable=False),
        sa.Column('medico_id',   sa.Integer(), nullable=True),
        sa.Column('observacoes', sa.Text(),    nullable=True),
        sa.Column('criado_em',   sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['consulta_id'], ['consultas.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['paciente_id'], ['pacientes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['medico_id'],   ['medicos.id'],   ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )
    op.create_index('ix_prescricoes_consulta_id', 'prescricoes', ['consulta_id'])

    # ── prescricao_itens ─────────────────────────────
    op.create_table(
        'prescricao_itens',
        sa.Column('id',             sa.Integer(),    nullable=False, autoincrement=True),
        sa.Column('prescricao_id',  sa.Integer(),    nullable=False),
        sa.Column('medicamento_id', sa.Integer(),    nullable=False),
        sa.Column('dose',           sa.String(100),  nullable=True),
        sa.Column('frequencia',     sa.String(100),  nullable=True),
        sa.Column('duracao',        sa.String(100),  nullable=True),
        sa.Column('instrucoes',     sa.Text(),       nullable=True),
        sa.ForeignKeyConstraint(['prescricao_id'],  ['prescricoes.id'],  ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['medicamento_id'], ['medicamentos.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )

    # ── consulta_id em exames ────────────────────────
    op.add_column('exames', sa.Column('consulta_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_exames_consulta_id', 'exames', 'consultas',
        ['consulta_id'], ['id'], ondelete='SET NULL'
    )
    op.create_index('ix_exames_consulta_id', 'exames', ['consulta_id'])


def downgrade() -> None:
    op.drop_index('ix_exames_consulta_id', table_name='exames')
    op.drop_constraint('fk_exames_consulta_id', 'exames', type_='foreignkey')
    op.drop_column('exames', 'consulta_id')
    op.drop_table('prescricao_itens')
    op.drop_index('ix_prescricoes_consulta_id', table_name='prescricoes')
    op.drop_table('prescricoes')
    op.drop_table('medicamentos')

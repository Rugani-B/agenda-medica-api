"""add a_marcar to status_exame enum

Revision ID: b5e3f1a2c8d6
Revises: 7c4d1e2f8a09
Create Date: 2026-06-11 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b5e3f1a2c8d6'
down_revision: Union[str, Sequence[str], None] = '7c4d1e2f8a09'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE exames MODIFY COLUMN status "
        "ENUM('a_marcar','agendado','realizado','cancelado') NULL"
    )


def downgrade() -> None:
    # Remove 'a_marcar' — registros com esse valor serão NULL após o downgrade
    op.execute(
        "ALTER TABLE exames MODIFY COLUMN status "
        "ENUM('agendado','realizado','cancelado') NULL"
    )

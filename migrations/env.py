# migrations/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Adiciona o caminho do projeto ao sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Importa o Base e TODOS os models (obrigatório para autogenerate)
from app.database.connection import engine
from app.database.base import Base

from app.models.pacientes       import Paciente
from app.models.medico         import Medico
from app.models.consulta       import Consulta
from app.models.confirmacao    import Confirmacao
from app.models.especialidade  import Especialidade
from app.models.reagendamento  import Reagendamento
from app.models.responsavel    import Responsavel
from app.models.log            import Log
from app.models.usuario        import Usuario
from app.models.pacientes     import Paciente
from app.models.medico        import Medico
from app.models.exame         import Exame
from app.models.local_exame   import LocalExame
from app.models.tipo_exame    import TipoExame
from app.models.anexo_exame   import AnexoExame
from app.models.medicamento   import Medicamento
from app.models.prescricao    import Prescricao, PrescricaoItem
from app.models.pedido_exame  import PedidoExame

config = context.config
fileConfig(config.config_file_name)

# Aponta para os metadata dos seus models
target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

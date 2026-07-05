from app.database.connection import engine
from app.database.base import Base

# Importar todos os models
from app.models.pacientes       import Paciente
from app.models.responsavel     import Responsavel
from app.models.especialidade   import Especialidade
from app.models.medico          import Medico
from app.models.consulta        import Consulta
from app.models.confirmacao     import Confirmacao
from app.models.reagendamento   import Reagendamento
from app.models.usuario         import Usuario
from app.models.tipo_exame      import TipoExame
from app.models.local_exame     import LocalExame
from app.models.exame           import Exame

from app.models.log             import Log


def init_db():
    print("Criando tabelas no banco MySQL...")
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas com sucesso.")


#if __name__ == "__main__":
#    init_db()

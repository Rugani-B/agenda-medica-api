from app.repositorios.exame_repository import ExameRepository
from app.models.exame import StatusExame


class ExameService:
    def __init__(self, db):
        self.repo = ExameRepository(db)

    def buscar_todos(self):
        return self.repo.buscar_todos()

    def buscar_por_id(self, id: int):
        return self.repo.buscar_por_id(id)

    def cadastrar(self, dados: dict):
        if not dados.get("paciente_id"):
            raise ValueError("Paciente é obrigatório.")
        if not dados.get("tipo_exame_id"):
            raise ValueError("Tipo de exame é obrigatório.")
        if not dados.get("local_id"):
            raise ValueError("Local é obrigatório.")
        if not dados.get("data_hora"):
            raise ValueError("Data/hora é obrigatória.")
        return self.repo.criar(dados)

    def atualizar(self, id: int, dados: dict):
        return self.repo.atualizar(id, dados)

    def deletar(self, id: int):
        return self.repo.deletar(id)

    def atualizar_status(self, id: int, status: StatusExame):
        return self.repo.atualizar_status(id, status)

    def filtrar(self, texto=None, status=None, paciente_id=None,
                dt_inicio=None, dt_fim=None):
        return self.repo.filtrar(
            texto=texto, status=status, paciente_id=paciente_id,
            dt_inicio=dt_inicio, dt_fim=dt_fim,
        )

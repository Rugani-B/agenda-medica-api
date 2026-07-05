from app.repositorios.tipo_exame_repository import TipoExameRepository


class TipoExameService:
    def __init__(self, db):
        self.repo = TipoExameRepository(db)

    def buscar_todos(self):
        return self.repo.buscar_todos()

    def cadastrar(self, dados: dict):
        if not dados.get("nome"):
            raise ValueError("Nome é obrigatório.")
        return self.repo.criar(dados)

    def atualizar(self, id: int, dados: dict):
        return self.repo.atualizar(id, dados)

    def deletar(self, id: int):
        return self.repo.deletar(id)

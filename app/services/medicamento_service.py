from app.repositorios.medicamento_repository import MedicamentoRepository


class MedicamentoService:
    def __init__(self, db):
        self.repo = MedicamentoRepository(db)

    def buscar_todos(self):
        return self.repo.buscar_todos()

    def buscar_por_nome(self, texto: str):
        return self.repo.buscar_por_nome(texto)

    def buscar_por_id(self, id: int):
        return self.repo.buscar_por_id(id)

    def cadastrar(self, dados: dict):
        if not dados.get("nome", "").strip():
            raise ValueError("Nome do medicamento é obrigatório.")
        return self.repo.criar(dados)

    def atualizar(self, id: int, dados: dict):
        if "nome" in dados and not dados["nome"].strip():
            raise ValueError("Nome do medicamento é obrigatório.")
        return self.repo.atualizar(id, dados)

    def deletar(self, id: int):
        return self.repo.deletar(id)

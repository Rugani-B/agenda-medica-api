from app.repositorios.base_repository import BaseRepository
from app.models.medicamento import Medicamento


class MedicamentoRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(Medicamento, db)

    def buscar_todos(self):
        return self.db.query(Medicamento).order_by(Medicamento.nome).all()

    def buscar_por_nome(self, texto: str):
        return (
            self.db.query(Medicamento)
            .filter(Medicamento.nome.ilike(f"%{texto}%"))
            .order_by(Medicamento.nome)
            .all()
        )

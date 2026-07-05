# app/repositorios/reagendamento_repository.py
from sqlalchemy.orm import Session
from app.models.reagendamento import Reagendamento
from app.repositorios.base_repository import BaseRepository


class ReagendamentoRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(Reagendamento, db)

    def buscar_por_consulta(self, consulta_id: int):
        return (
            self.db.query(Reagendamento)
            .filter(Reagendamento.consulta_id == consulta_id)
            .order_by(Reagendamento.reagendado_em)
            .all()
        )

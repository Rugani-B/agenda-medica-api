# app/repositorios/medico_repository.py
from sqlalchemy.orm import Session
from app.models.medico import Medico
from app.repositorios.base_repository import BaseRepository


class MedicoRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(Medico, db)

    def buscar_por_crm(self, crm: str):
        return self.db.query(Medico).filter(Medico.crm == crm).first()

    def buscar_por_especialidade(self, especialidade_id: int):
        return (
            self.db.query(Medico)
            .filter(Medico.especialidade_id == especialidade_id)
            .order_by(Medico.nome)
            .all()
        )

    def buscar_por_nome(self, nome: str):
        return (
            self.db.query(Medico)
            .filter(Medico.nome.ilike(f"%{nome}%"))
            .all()
        )

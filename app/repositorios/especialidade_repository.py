# app/repositorios/especialidade_repository.py
from sqlalchemy.orm import Session
from app.models import Especialidade
from app.repositorios.base_repository import BaseRepository


class EspecialidadeRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(Especialidade, db)

    def buscar_por_nome(self, nome: str):
        return (
            self.db.query(Especialidade)
            .filter(Especialidade.nome.ilike(f"%{nome}%"))
            .all()
        )

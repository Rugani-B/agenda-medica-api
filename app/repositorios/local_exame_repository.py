from sqlalchemy.orm import Session
from app.models.local_exame import LocalExame
from app.repositorios.base_repository import BaseRepository


class LocalExameRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(LocalExame, db)

    def buscar_por_nome(self, nome: str):
        return (
            self.db.query(LocalExame)
            .filter(LocalExame.nome.ilike(f"%{nome}%"))
            .all()
        )

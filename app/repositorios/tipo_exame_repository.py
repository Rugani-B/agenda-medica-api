from sqlalchemy.orm import Session
from app.models.tipo_exame import TipoExame
from app.repositorios.base_repository import BaseRepository


class TipoExameRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(TipoExame, db)

    def buscar_por_nome(self, nome: str):
        return (
            self.db.query(TipoExame)
            .filter(TipoExame.nome.ilike(f"%{nome}%"))
            .all()
        )

from app.repositorios.base_repository import BaseRepository
from app.models.anexo_exame import AnexoExame


class AnexoExameRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(AnexoExame, db)

    def buscar_por_exame(self, exame_id: int):
        return (
            self.db.query(AnexoExame)
            .filter(AnexoExame.exame_id == exame_id)
            .order_by(AnexoExame.criado_em)
            .all()
        )

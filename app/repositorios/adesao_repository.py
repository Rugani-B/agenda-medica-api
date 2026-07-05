from app.repositorios.base_repository import BaseRepository
from app.models.adesao_tratamento import AdesaoTratamento
import datetime


class AdesaoRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(AdesaoTratamento, db)

    def buscar_por_prescricao(self, prescricao_id: int):
        return (
            self.db.query(AdesaoTratamento)
            .filter(AdesaoTratamento.prescricao_id == prescricao_id)
            .order_by(AdesaoTratamento.semana)
            .all()
        )

    def buscar_por_semana(self, prescricao_id: int, semana: datetime.date):
        return (
            self.db.query(AdesaoTratamento)
            .filter(
                AdesaoTratamento.prescricao_id == prescricao_id,
                AdesaoTratamento.semana == semana,
            )
            .first()
        )

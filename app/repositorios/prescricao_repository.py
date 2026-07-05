from app.repositorios.base_repository import BaseRepository
from app.models.prescricao import Prescricao, PrescricaoItem


class PrescricaoRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(Prescricao, db)

    def buscar_por_consulta(self, consulta_id: int):
        return (
            self.db.query(Prescricao)
            .filter(Prescricao.consulta_id == consulta_id)
            .order_by(Prescricao.criado_em)
            .all()
        )

    def buscar_todas(self):
        return (
            self.db.query(Prescricao)
            .order_by(Prescricao.criado_em.desc())
            .all()
        )

    def buscar_por_paciente(self, paciente_id: int):
        return (
            self.db.query(Prescricao)
            .filter(Prescricao.paciente_id == paciente_id)
            .order_by(Prescricao.criado_em.desc())
            .all()
        )

    def adicionar_item(self, dados: dict) -> PrescricaoItem:
        item = PrescricaoItem(**dados)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def remover_item(self, item_id: int):
        item = self.db.query(PrescricaoItem).filter(PrescricaoItem.id == item_id).first()
        if item:
            self.db.delete(item)
            self.db.commit()

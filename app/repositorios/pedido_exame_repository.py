from app.repositorios.base_repository import BaseRepository
from app.models.pedido_exame import PedidoExame, StatusPedido


class PedidoExameRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(PedidoExame, db)

    def buscar_por_consulta(self, consulta_id: int):
        return (
            self.db.query(PedidoExame)
            .filter(PedidoExame.consulta_id == consulta_id)
            .order_by(PedidoExame.criado_em)
            .all()
        )

    def buscar_por_paciente(self, paciente_id: int):
        return (
            self.db.query(PedidoExame)
            .filter(PedidoExame.paciente_id == paciente_id)
            .order_by(PedidoExame.criado_em.desc())
            .all()
        )

    def filtrar(self, status=None, paciente_id=None, medico_id=None):
        query = self.db.query(PedidoExame)
        if status:
            query = query.filter(PedidoExame.status == status)
        if paciente_id:
            query = query.filter(PedidoExame.paciente_id == paciente_id)
        if medico_id:
            query = query.filter(PedidoExame.medico_id == medico_id)
        return query.order_by(PedidoExame.criado_em.desc()).all()

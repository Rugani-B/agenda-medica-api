from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.database.base import Base


class StatusPedido(Enum):
    solicitado = "solicitado"
    agendado   = "agendado"
    realizado  = "realizado"
    cancelado  = "cancelado"


class PedidoExame(Base):
    __tablename__ = "pedidos_exame"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    consulta_id   = Column(Integer, ForeignKey("consultas.id",   ondelete="SET NULL"),  nullable=True)
    paciente_id   = Column(Integer, ForeignKey("pacientes.id",   ondelete="CASCADE"),   nullable=False)
    medico_id     = Column(Integer, ForeignKey("medicos.id",     ondelete="SET NULL"),  nullable=True)
    tipo_exame_id = Column(Integer, ForeignKey("tipos_exame.id", ondelete="RESTRICT"),  nullable=False)
    exame_id      = Column(Integer, ForeignKey("exames.id",      ondelete="SET NULL"),  nullable=True)
    urgente       = Column(Boolean, default=False, nullable=False)
    observacoes   = Column(Text,    nullable=True)
    status        = Column(SAEnum(StatusPedido), default=StatusPedido.solicitado, nullable=False)
    criado_em     = Column(DateTime, default=datetime.utcnow)
    documento_path = Column(String(500), nullable=True)   # caminho do PDF/JPG do pedido de exame

    consulta   = relationship("Consulta",  back_populates="pedidos_exame")
    paciente   = relationship("Paciente")
    medico     = relationship("Medico")
    tipo_exame = relationship("TipoExame")
    exame      = relationship("Exame")

    def __repr__(self):
        return f"<PedidoExame {self.id} - {self.tipo_exame_id}>"

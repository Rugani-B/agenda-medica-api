from sqlalchemy import Column, Integer, Text, DateTime, Enum, ForeignKey, Index
from sqlalchemy.sql import func
import enum
from sqlalchemy.orm import relationship

from app.models.base_enums import StatusAgendamento
from app.database.base import Base

class StatusConsulta(enum.Enum):
    agendada = "agendada"
    confirmada = "confirmada"
    reagendada = "reagendada"
    cancelada = "cancelada"
    realizada = "realizada"


class Consulta(Base):
    __tablename__ = "consultas"

    __table_args__ = (
        Index("idx_consultas_data",     "data_hora"),
        Index("idx_consultas_paciente", "paciente_id"),
        Index("idx_consultas_medico",   "medico_id"),     )

    id              = Column(Integer, primary_key=True)
    paciente_id     = Column(Integer, ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False    )
    medico_id       = Column(Integer, ForeignKey("medicos.id", ondelete="SET NULL")    )
    data_hora       = Column(DateTime(timezone=True), nullable=False)
    status          = Column(Enum(StatusAgendamento), nullable=False, default=StatusAgendamento.agendada)
    observacoes     = Column(Text)
    criado_em       = Column(DateTime(timezone=True), server_default=func.now())

    paciente        = relationship("Paciente",       back_populates="consultas")
    medico          = relationship("Medico",         back_populates="consultas")
    confirmacoes    = relationship("Confirmacao",    back_populates="consulta", cascade="all, delete-orphan")
    reagendamentos  = relationship("Reagendamento",  back_populates="consulta", cascade="all, delete-orphan")
    prescricoes     = relationship("Prescricao",   back_populates="consulta", cascade="all, delete-orphan")
    exames          = relationship("Exame",         back_populates="consulta")
    pedidos_exame   = relationship("PedidoExame",  back_populates="consulta", cascade="all, delete-orphan")


from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.database.base import Base


class StatusExame(Enum):
    a_marcar  = "a_marcar"
    agendado  = "agendado"
    realizado = "realizado"
    cancelado = "cancelado"


class Exame(Base):
    __tablename__ = "exames"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    paciente_id    = Column(Integer, ForeignKey("pacientes.id"),    nullable=False)
    consulta_id    = Column(Integer, ForeignKey("consultas.id",  ondelete="SET NULL"), nullable=True)
    tipo_exame_id  = Column(Integer, ForeignKey("tipos_exame.id"),  nullable=False)
    local_id       = Column(Integer, ForeignKey("locais_exame.id"), nullable=False)
    medico_id      = Column(Integer, ForeignKey("medicos.id"),      nullable=True)
    data_hora      = Column(DateTime, nullable=False)
    status         = Column(SAEnum(StatusExame), default=StatusExame.agendado)
    observacoes    = Column(Text, nullable=True)
    resultado      = Column(Text, nullable=True)
    criado_em      = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    paciente   = relationship("Paciente",   back_populates="exames")
    consulta   = relationship("Consulta",   back_populates="exames")
    tipo_exame = relationship("TipoExame")
    local      = relationship("LocalExame")
    medico     = relationship("Medico")
    anexos     = relationship("AnexoExame", back_populates="exame",
                              cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Exame {self.id} - {self.tipo_exame}>"

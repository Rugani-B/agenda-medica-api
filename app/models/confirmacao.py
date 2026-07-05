import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy import Column, Integer, Text, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class StatusConfirmacao(enum.Enum):
    agendada    = "agendada"
    confirmada  = "confirmada"
    reagendada  = "reagendada"
    cancelada   = "cancelada"
    realizada   = "realizada"


class Confirmacao(Base):
    __tablename__ = "confirmacoes"

    id              = Column(Integer, primary_key=True)
    consulta_id     = Column(Integer, ForeignKey("consultas.id", ondelete="CASCADE"), nullable=False    )
    enviado_em      = Column(DateTime(timezone=True))
    canal           = Column(Text)  # fiel ao SQL
    status          = Column(Enum(StatusConfirmacao), nullable=False, default=StatusConfirmacao.agendada    )
    respondido_em   = Column(DateTime(timezone=True))
    respondido      = Column(Text)

    consulta = relationship("Consulta", back_populates="confirmacoes")

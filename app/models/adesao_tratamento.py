from sqlalchemy import Column, Integer, Text, Date, DateTime, ForeignKey, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.database.base import Base


class NivelAdesao(Enum):
    nenhuma = "nenhuma"
    baixa   = "baixa"
    parcial = "parcial"
    boa     = "boa"
    total   = "total"


NIVEL_LABELS = {
    "nenhuma": ("Nenhuma",  "0%",    "#888780"),
    "baixa"  : ("Baixa",   "até 25%","#E24B4A"),
    "parcial": ("Parcial", "até 50%","#EF9F27"),
    "boa"    : ("Boa",     "até 75%","#378ADD"),
    "total"  : ("Total",   "100%",   "#639922"),
}

NIVEL_PCT = {
    "nenhuma": 0,
    "baixa"  : 25,
    "parcial": 50,
    "boa"    : 75,
    "total"  : 100,
}


class AdesaoTratamento(Base):
    __tablename__ = "adesao_tratamento"
    __table_args__ = (
        UniqueConstraint("prescricao_id", "semana", name="uq_adesao_prescricao_semana"),
    )

    id            = Column(Integer,  primary_key=True, autoincrement=True)
    prescricao_id = Column(Integer,  ForeignKey("prescricoes.id", ondelete="CASCADE"), nullable=False)
    semana        = Column(Date,     nullable=False)
    nivel         = Column(SAEnum(NivelAdesao), nullable=False)
    observacoes   = Column(Text,     nullable=True)
    registrado_em = Column(DateTime, default=datetime.utcnow)

    prescricao = relationship("Prescricao", back_populates="adesoes")

    def __repr__(self):
        return f"<AdesaoTratamento prescricao={self.prescricao_id} semana={self.semana} nivel={self.nivel}>"

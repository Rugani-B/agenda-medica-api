from sqlalchemy import Column, Index, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import Base
 

class Medico(Base):
    __tablename__ = "medicos"

    __table_args__ = (
        Index("idx_medicos_especialidade", "especialidade_id"), )

    id                  =   Column(Integer, primary_key=True)
    nome                =   Column(String(100), nullable=False)
    crm                 =   Column(String(20), unique=True)
    especialidade_id    =   Column(Integer, ForeignKey("especialidades.id", ondelete="SET NULL"))
    clinica             =   Column(String(150))
    telefone            =   Column(String(20))
    observacoes         =   Column(Text)

    especialidade = relationship("Especialidade", back_populates="medicos")
    consultas     = relationship("Consulta",      back_populates="medico")
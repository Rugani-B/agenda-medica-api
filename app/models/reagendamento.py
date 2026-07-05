from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database.base import Base
from sqlalchemy.orm import relationship


class Reagendamento(Base):
    __tablename__ = "reagendamentos"

    id              =   Column(Integer, primary_key=True)
    consulta_id     =   Column(Integer, ForeignKey("consultas.id", ondelete="CASCADE"), nullable=False)
    data_anterior   =   Column(DateTime(timezone=True))
    nova_data       =   Column(DateTime(timezone=True))
    motivo          =   Column(Text)
    reagendado_por  =   Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"))
    reagendado_em   =   Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    consulta = relationship("Consulta", back_populates="reagendamentos")
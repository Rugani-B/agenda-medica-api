from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, LargeBinary
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.base import Base



class Responsavel(Base):
    __tablename__ = "responsaveis"

    id              =   Column(Integer, primary_key=True)
    paciente_id     =   Column(Integer, ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False)
    nome            =   Column(String(100), nullable=False)
    parentesco      =   Column(String(50))
    telefone        =   Column(String(20))
    whatsapp        =   Column(String(20))
    email           =   Column(String(100))
    observacoes     =   Column(Text)
    senha_hash      =   Column(LargeBinary, nullable=True)   # senha do link do portal familiar (bcrypt)
    criado_em       =   Column(DateTime(timezone=True), server_default=func.now())

    paciente = relationship("Paciente", back_populates="responsaveis")
 
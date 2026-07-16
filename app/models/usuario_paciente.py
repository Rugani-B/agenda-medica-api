from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base


class UsuarioPaciente(Base):
    __tablename__ = "usuario_paciente"

    id          = Column(Integer, primary_key=True)
    usuario_id  = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    paciente_id = Column(Integer, ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False)
    criado_em   = Column(DateTime(timezone=True), server_default=func.now())

    usuario = relationship("Usuario", backref="vinculos_pacientes")
    paciente = relationship("Paciente", backref="vinculos_usuarios")

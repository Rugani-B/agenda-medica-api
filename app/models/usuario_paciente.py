from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base


class UsuarioPaciente(Base):
    __tablename__ = "usuario_paciente"

    id                = Column(Integer, primary_key=True)
    usuario_id        = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    paciente_id       = Column(Integer, ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False)
    status            = Column(String(10), nullable=False, default="pendente")  # pendente | ativo
    nivel             = Column(Integer, nullable=True)    # 1=agenda, 2=acompanhamento, 3=completo
    protocolo_origem  = Column(String(50), nullable=True) # protocolo do consentimento que originou o vínculo
    criado_em         = Column(DateTime(timezone=True), server_default=func.now())

    usuario = relationship("Usuario", backref="vinculos_pacientes")
    paciente = relationship("Paciente", backref="vinculos_usuarios")

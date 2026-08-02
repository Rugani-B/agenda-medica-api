from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from app.database.base import Base


class LogAuditoria(Base):
    __tablename__ = "logs_auditoria"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id  = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id", ondelete="SET NULL"), nullable=True)
    acao        = Column(String(20),  nullable=False)  # leitura | criacao | edicao | exclusao | login | revogacao
    recurso     = Column(String(50),  nullable=False)  # consultas | exames | prescricoes | adesao | consentimento ...
    recurso_id  = Column(Integer,     nullable=True)
    ip          = Column(String(45),  nullable=True)
    user_agent  = Column(String(500), nullable=True)
    criado_em   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    detalhes    = Column(JSON,        nullable=True)   # contexto extra livre

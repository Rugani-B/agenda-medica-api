from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Index
from sqlalchemy.sql import func
from app.database.base import Base
import enum


class AcaoLog(enum.Enum):
    insercao    =   "insercao"
    atualizacao =   "atualizacao"
    exclusao    =   "exclusao"
    login       =   "login"
    logout      =   "logout"
    erro        =   "erro"


class Log(Base):
    __tablename__ = "logs"

    __table_args__ = (
        Index("idx_logs_usuario", "usuario_id"),
        Index("idx_logs_tabela_registro", "tabela", "registro_id"), )
    

    id              = Column(Integer, primary_key=True)
    usuario_id      = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL")    )
    tabela          = Column(String(50))
    registro_id     = Column(Integer)
    ip_origem       = Column(String(45))
    acao            = Column(Enum(AcaoLog),nullable=False  )
    descricao       = Column(Text)
    criado_em       = Column(DateTime(timezone=True), server_default=func.now())

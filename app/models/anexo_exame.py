from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base


class AnexoExame(Base):
    __tablename__ = "anexos_exame"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    exame_id   = Column(Integer, ForeignKey("exames.id", ondelete="CASCADE"), nullable=False)
    nome       = Column(String(255), nullable=False)   # nome exibido ao usuário
    caminho    = Column(String(1024), nullable=False)  # caminho absoluto no disco
    tipo       = Column(String(20),  nullable=False)   # 'pdf' | 'imagem'
    criado_em  = Column(DateTime, default=datetime.utcnow)

    exame = relationship("Exame", back_populates="anexos")

    def __repr__(self):
        return f"<AnexoExame {self.id} - {self.nome}>"

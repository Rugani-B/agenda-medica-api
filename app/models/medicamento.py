from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base


class Medicamento(Base):
    __tablename__ = "medicamentos"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    nome            = Column(String(200), nullable=False)
    principio_ativo = Column(String(200), nullable=True)
    apresentacao    = Column(String(100), nullable=True)   # comprimido, cápsula, solução…
    criado_em       = Column(DateTime, default=datetime.utcnow)

    itens = relationship("PrescricaoItem", back_populates="medicamento")

    def __repr__(self):
        return f"<Medicamento {self.id} - {self.nome}>"

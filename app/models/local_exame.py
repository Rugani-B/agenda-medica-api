from sqlalchemy import Column, Integer, String
from app.database.base import Base


class LocalExame(Base):
    __tablename__ = "locais_exame"

    id       = Column(Integer, primary_key=True, autoincrement=True)
    nome     = Column(String(150), nullable=False)
    endereco = Column(String(255), nullable=True)
    telefone = Column(String(20),  nullable=True)
    tipo     = Column(String(50),  nullable=True)  # hospital, clínica, laboratório

    def __repr__(self):
        return f"<LocalExame {self.nome}>"

from sqlalchemy import Column, Integer, String
from app.database.base import Base
from sqlalchemy.orm import relationship


class Especialidade(Base):
    __tablename__ = "especialidades"

    id = Column(Integer, primary_key=True)
    nome = Column(String(100), unique=True, nullable=False)

    # Relationship
    medicos = relationship("Medico", back_populates="especialidade")
from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import date

from app.database.base import Base


class Paciente(Base):
    __tablename__ = "pacientes"



    id                  = Column(Integer, primary_key=True)
    nome                = Column(String(100), nullable=False)
    data_nascimento     = Column(Date, nullable=False)
    cpf                 = Column(String(14), unique=True)
    telefone            = Column(String(20))
    email               = Column(String(100))
    contato_emergencia  = Column(String(100))
    tel_emergencia      = Column(String(20))
    ativo               = Column(Boolean, default=True)
    criado_em           = Column(DateTime(timezone=True), server_default=func.now())


    @property
    def idade(self) -> int:
        hoje = date.today()
        return hoje.year - self.data_nascimento.year - (
            (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day)
        )

    responsaveis    = relationship("Responsavel", back_populates="paciente", cascade="all, delete-orphan")
    consultas       = relationship("Consulta",    back_populates="paciente")
    exames          = relationship("Exame", back_populates="paciente")


from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base


class Prescricao(Base):
    __tablename__ = "prescricoes"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    consulta_id = Column(Integer, ForeignKey("consultas.id", ondelete="CASCADE"), nullable=False)
    paciente_id = Column(Integer, ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False)
    medico_id   = Column(Integer, ForeignKey("medicos.id",   ondelete="SET NULL"), nullable=True)
    observacoes    = Column(Text,     nullable=True)
    criado_em      = Column(DateTime, default=datetime.utcnow)
    semana_inicio  = Column(Date,     nullable=True)   # segunda-feira de início do tratamento
    semana_fim     = Column(Date,     nullable=True)   # segunda-feira da última semana do tratamento

    consulta  = relationship("Consulta",       back_populates="prescricoes")
    paciente  = relationship("Paciente")
    medico    = relationship("Medico")
    itens   = relationship("PrescricaoItem",    back_populates="prescricao",
                           cascade="all, delete-orphan")
    adesoes = relationship("AdesaoTratamento", back_populates="prescricao",
                           cascade="all, delete-orphan", order_by="AdesaoTratamento.semana")

    def __repr__(self):
        return f"<Prescricao {self.id} consulta={self.consulta_id}>"


class PrescricaoItem(Base):
    __tablename__ = "prescricao_itens"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    prescricao_id  = Column(Integer, ForeignKey("prescricoes.id", ondelete="CASCADE"), nullable=False)
    medicamento_id = Column(Integer, ForeignKey("medicamentos.id", ondelete="RESTRICT"), nullable=False)
    dose           = Column(String(100), nullable=True)   # ex: "500mg"
    frequencia     = Column(String(100), nullable=True)   # ex: "8 em 8 horas"
    duracao        = Column(String(100), nullable=True)   # ex: "7 dias"
    instrucoes     = Column(Text,        nullable=True)   # ex: "tomar após refeição"

    prescricao  = relationship("Prescricao",  back_populates="itens")
    medicamento = relationship("Medicamento", back_populates="itens")

    def __repr__(self):
        return f"<PrescricaoItem {self.id} med={self.medicamento_id}>"

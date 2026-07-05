# app/repositorios/paciente_repository.py
from sqlalchemy.orm import Session
from app.models.pacientes import Paciente
from app.repositorios.base_repository import BaseRepository


class PacienteRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(Paciente, db)

    def buscar_por_cpf(self, cpf: str):
        return self.db.query(Paciente).filter(Paciente.cpf == cpf).first()

    def buscar_por_nome(self, nome: str):
        return (
            self.db.query(Paciente)
            .filter(Paciente.nome.ilike(f"%{nome}%"))
            .all()
        )

    def buscar_ativos(self):
        return (
            self.db.query(Paciente)
            .filter(Paciente.ativo == True)
            .order_by(Paciente.nome)
            .all()
        )

    def desativar(self, id: int):
        paciente = self.buscar_por_id(id)
        if paciente:
            paciente.ativo = False
            self.db.commit()
            self.db.refresh(paciente)
        return paciente

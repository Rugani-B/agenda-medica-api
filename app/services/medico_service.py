# app/services/medico_service.py
from sqlalchemy.orm import Session
from app.models.medico import Medico
from app.repositorios.medico_repository import MedicoRepository


class MedicoService:
    def __init__(self, db: Session):
        self.repo = MedicoRepository(db)

    def cadastrar(self, dados: dict) -> Medico:
        # Verifica CRM duplicado
        if dados.get("crm"):
            existente = self.repo.buscar_por_crm(dados["crm"])
            if existente:
                raise ValueError(f"CRM {dados['crm']} já cadastrado.")

        medico = Medico(**dados)
        return self.repo.salvar(medico)

    def atualizar(self, id: int, dados: dict) -> Medico:
        medico = self.repo.buscar_por_id(id)
        if not medico:
            raise ValueError("Médico não encontrado.")

        # Verifica CRM duplicado se estiver sendo alterado
        if "crm" in dados and dados["crm"] != medico.crm:
            existente = self.repo.buscar_por_crm(dados["crm"])
            if existente:
                raise ValueError(f"CRM {dados['crm']} já cadastrado.")

        for campo, valor in dados.items():
            setattr(medico, campo, valor)

        return self.repo.salvar(medico)

    def buscar_por_especialidade(self, especialidade_id: int):
        return self.repo.buscar_por_especialidade(especialidade_id)

    def buscar_por_nome(self, nome: str):
        return self.repo.buscar_por_nome(nome)

    def buscar_por_id(self, id: int) -> Medico:
        medico = self.repo.buscar_por_id(id)
        if not medico:
            raise ValueError("Médico não encontrado.")
        return medico

    def buscar_todos(self):
        return self.repo.buscar_todos()

    def deletar(self, id: int):
        medico = self.repo.buscar_por_id(id)
        if not medico:
            raise ValueError("Médico não encontrado.")
        return self.repo.deletar(id)

# app/services/paciente_service.py
from sqlalchemy.orm import Session
from app.models.pacientes import Paciente
from app.repositorios.paciente_repository import PacienteRepository


class PacienteService:
    def __init__(self, db: Session):
        self.repo = PacienteRepository(db)

    def cadastrar(self, dados: dict) -> Paciente:
        # Verifica CPF duplicado
        if dados.get("cpf"):
            existente = self.repo.buscar_por_cpf(dados["cpf"])
            if existente:
                raise ValueError(f"CPF {dados['cpf']} já cadastrado.")

        paciente = Paciente(**dados)
        return self.repo.salvar(paciente)

    def atualizar(self, id: int, dados: dict) -> Paciente:
        paciente = self.repo.buscar_por_id(id)
        if not paciente:
            raise ValueError("Paciente não encontrado.")

        # Verifica CPF duplicado se estiver sendo alterado
        if "cpf" in dados and dados["cpf"] != paciente.cpf:
            existente = self.repo.buscar_por_cpf(dados["cpf"])
            if existente:
                raise ValueError(f"CPF {dados['cpf']} já cadastrado.")

        for campo, valor in dados.items():
            setattr(paciente, campo, valor)

        return self.repo.salvar(paciente)

    def desativar(self, id: int) -> Paciente:
        paciente = self.repo.buscar_por_id(id)
        if not paciente:
            raise ValueError("Paciente não encontrado.")
        return self.repo.desativar(id)

    def buscar_por_nome(self, nome: str):
        return self.repo.buscar_por_nome(nome)

    def buscar_ativos(self):
        return self.repo.buscar_ativos()

    def buscar_por_id(self, id: int) -> Paciente:
        paciente = self.repo.buscar_por_id(id)
        if not paciente:
            raise ValueError("Paciente não encontrado.")
        return paciente

    def buscar_todos(self):
        return self.repo.buscar_todos()  # retorna todos, inclusive inativos